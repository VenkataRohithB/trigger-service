import json
import re
from fastapi import Depends, Body, Request, APIRouter, Query
from fastapi.security import HTTPAuthorizationCredentials

from om_helper import *
from db_helper import *
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict
from pubsub_helper import PubSub

router = APIRouter(tags=["trigger"])

TIME_PATTERN = r"^\d{4}-\d{2}-\d{2}-\d{2}:\d{2}$"


def check_trigger_time(trigger_time: str = None, interval: int = None, present: bool = False):
    if not trigger_time and not interval:
        return {"message": "Both 'trigger_time' and 'interval' cannot be None", "status_bool": False}

    current_time = datetime.now().replace(second=0, microsecond=0)

    if not trigger_time:
        trigger_time = current_time.strftime("%Y-%m-%d-%H:%M")

    if not re.match(TIME_PATTERN, trigger_time):
        return {"message": "Invalid format. Use YYYY-MM-DD-HH:mm", "status_bool": False}

    try:
        parsed_time = datetime.strptime(trigger_time, "%Y-%m-%d-%H:%M").replace(second=0, microsecond=0)
        if interval:
            parsed_time += timedelta(minutes=interval)
        if parsed_time < current_time or (present and parsed_time == current_time):
            return {"message": "Trigger time must be in the future", "status_bool": False}

    except ValueError:
        return {"message": "Invalid date. Use a valid YYYY-MM-DD-HH:mm", "status_bool": False}

    return {"status_bool": True, "trigger_time": parsed_time}


class CreateTriggerRequest(BaseModel):
    trigger_name: str = Field(..., description="Name of your trigger")
    trigger_time: Optional[str] = Field(None, description="Trigger time in format YYYY-MM-DD-HH:mm")
    last_triggered_on: Optional[str] = Field(None, description="Lastly triggered time in YYYY-MM-DD-HH:mm")
    trigger_count: Optional[int] = Field(None, description="Count of no of times triggered in numbers")
    interval: Optional[int] = Field(None, description="Interval in minutes")
    trigger_message: Optional[str] = Field("", description="Message to be displayed when triggered")
    api_payload: Optional[Dict[str, str]] = Field(default=None, description="API payload if it's an API trigger")


@router.post("/triggers/create_trigger")
@authorize_token
async def create_trigger(
        request: Request,
        data: CreateTriggerRequest,
        token: HTTPAuthorizationCredentials = Depends(security),
):
    is_api_trigger = bool(data.api_payload)
    trigger_type = "api" if is_api_trigger else "scheduled"

    parsed_time = (
        datetime.now().replace(second=0, microsecond=0)
        if is_api_trigger
        else None
    )
    last_triggered = None
    if not is_api_trigger:
        validate_response = check_trigger_time(trigger_time=data.trigger_time, interval=data.interval)
        if not validate_response["status_bool"]:
            return failure_json(message=validate_response["message"], status_code=S_BADREQUEST_CODE)
        parsed_time = validate_response["trigger_time"]
        if data.last_triggered_on is not None:
            validate_response = check_trigger_time(trigger_time=data.last_triggered_on, present=True)
            if not validate_response["status_bool"]:
                return failure_json(message=validate_response["message"], status_code=S_BADREQUEST_CODE)
            last_triggered = validate_response["trigger_time"]

    insert_data = {
        "trigger_time": parsed_time,
        "interval": None if is_api_trigger else data.interval,
        "trigger_name": data.trigger_name,
        "trigger_message": data.trigger_message,
        "trigger_type": trigger_type,
        "api_payload": json.dumps(data.api_payload) if is_api_trigger else None,
        "last_triggered_on": last_triggered,
        "trigger_count": data.trigger_count
    }

    # if is_api_trigger:
    #     conn = PubSub(topic="TRIGGER_EVENTS")
    #     publish_message = insert_data
    #     publish_message["trigger_time"] = publish_message["trigger_time"].strftime("%Y-%m-%d %H:%M:%S")
    #     res = conn.publish(msg_dict=insert_data)
    #
    #     print(res,insert_data)

    response = insert_query(table_name=S_TRIGGER_TABLE, data=insert_data)

    if response["status_bool"]:
        if is_api_trigger:
            conn = PubSub(topic="TRIGGER_EVENTS")
            conn.publish(msg_dict=response["records"][0])
        return success_json(records=response["records"], message=f"Trigger '{data.trigger_name}' created successfully")

    return failure_json(message=f"Failed to create trigger: {response.get('message')}", status_code=S_BADREQUEST_CODE)


@router.get("/triggers/fetch")
@authorize_token
async def get_triggers(
        request: Request,
        trigger_id: int = Query(None, description="ID of the trigger record"),
        trigger_name: str = Query(None, description="Name of your trigger"),
        trigger_type: str = Query(None, description="Type of trigger api/scheduled"),
        num_records: int = Query(None, description="No of records to fetch"),
        token: HTTPAuthorizationCredentials = Depends(security)
):
    conditions = {}

    if trigger_id is not None:
        conditions["id"] = trigger_id
    if trigger_name is not None:
        conditions["trigger_name"] = trigger_name
    if trigger_type is not None:
        conditions["trigger_type"] = trigger_type

    response = select_query(table_name=S_TRIGGER_TABLE, conditions=conditions, num_records=num_records)
    if response:
        return success_json(records=response, message="Fetched triggers successfully")

    return failure_json(message="No Records Found", status_code=S_NOTFOUND_CODE)


@router.get("/triggered_events/current_time")
@authorize_token
async def get_logged_events(
        request: Request,
        token: HTTPAuthorizationCredentials = Depends(security)
):
    present_timeline = (datetime.now()).strftime("%Y-%m-%d %H:%M")
    conditions = {"trigger_time": present_timeline}
    response = select_query(table_name=S_TRIGGER_TABLE, conditions=conditions)
    if response:
        return success_json(records=response, message="Fetched triggered event logs successfully")

    return failure_json(message="No Records Found", status_code=S_NOTFOUND_CODE)


@router.patch("/triggers/update_trigger")
@authorize_token
async def update_triggers(
        request: Request,
        trigger_id: int = Query(..., description="ID of the trigger record"),
        data: dict = Body(..., description="Fields to be updated in JSON format"),
        token: HTTPAuthorizationCredentials = Depends(security)
):
    get_response = select_query(table_name=S_TRIGGER_TABLE, conditions={"id": trigger_id})
    if not get_response:
        return failure_json(message="Record not found", status_code=S_NOTFOUND_CODE)

    if "id" in data:
        return failure_json(message="Cannot change ID", status_code=S_FORBIDDEN_CODE)

    if get_response[0]["status"] == "inactive":
        return failure_json(message="Cannot change inactive triggers", status_code=S_FORBIDDEN_CODE)

    if "interval" in data:
        data["trigger_time"] = datetime.strptime(get_response[0]["trigger_time"], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d-%H:%M")

    if "trigger_time" in data:
        validate_response = check_trigger_time(trigger_time=data.get("trigger_time"), interval=data.get("interval"))
        if not validate_response["status_bool"]:
            return failure_json(message=validate_response["message"], status_code=S_BADREQUEST_CODE)
        data["trigger_time"] = validate_response["trigger_time"]

    if "last_triggered_on" in data:
        validate_response = check_trigger_time(trigger_time=data.get("last_triggered_on"), present=True)
        if not validate_response["status_bool"]:
            return failure_json(message=validate_response["message"], status_code=S_BADREQUEST_CODE)
        data["last_triggered_on"] = validate_response["trigger_time"]

    update_response = update_query(table_name=S_TRIGGER_TABLE, conditions={"id": trigger_id}, data=data)[0]
    if update_response and update_response["status_bool"]:
        return success_json(records=update_response["records"], message="Updated successfully")

    return failure_json(message=f"Something went wrong: {update_response.get('message')}",
                        status_code=S_BADREQUEST_CODE)


@router.delete("/triggers/delete_trigger")
@authorize_token
async def delete_trigger(request: Request, trigger_id: int, token: HTTPAuthorizationCredentials = Depends(security)):
    delete_response = delete_query(table_name=S_TRIGGER_TABLE, record_id=trigger_id)[0]
    if delete_response["status_bool"]:
        return success_json(records=[], message="Record Deleted Successfully")
    return failure_json(message=f"Cannot Delete Record, {delete_response['message']}", status_code=S_BADREQUEST_CODE)
