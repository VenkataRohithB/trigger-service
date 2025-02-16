import json
import re
from datetime import datetime, timedelta
from fastapi import Depends, Body, Request, APIRouter, Query
from fastapi.security import HTTPAuthorizationCredentials

from om_helper import *
from constants import *
from db_helper import *


class EventStatus(str, Enum):
    active = "active"
    archived = "archived"


def update_and_delete_records():
    archive_time = (datetime.now() - timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M")
    delete_time = (datetime.now() - timedelta(seconds=120)).strftime("%Y-%m-%d %H:%M")
    update_query = sql.SQL("""
        UPDATE {table}
        SET status = 'archived'
        WHERE triggered_at <= {archive_time} AND status = 'active'
        RETURNING *;
    """).format(
        table=sql.Identifier(S_TRIGGER_EVENTS_TABLE),
        archive_time=sql.Placeholder("archive_time")
    )
    delete_query = sql.SQL("""
        DELETE FROM {table}
        WHERE triggered_at <= {delete_time} AND status = 'archived'
        RETURNING *;
    """).format(
        table=sql.Identifier(S_TRIGGER_EVENTS_TABLE),
        delete_time=sql.Placeholder("delete_time")
    )
    update_response = execute_query(query=update_query, params={"archive_time": archive_time})
    delete_response = execute_query(query=delete_query, params={"delete_time": delete_time})

    return {
        "updated_records": update_response,
        "deleted_records": delete_response
    }

# ------------------------------------------------------------------------------------------------------


router = APIRouter(tags=["trigger_events"])


@router.post("/triggered_events/log_event")
@authorize_token
async def log_trigger_event(
        request: Request,
        trigger_id: int,
        token: HTTPAuthorizationCredentials = Depends(security)
):
    trigger_record = select_query(table_name=S_TRIGGER_TABLE, conditions={"id": trigger_id})[0]

    if not trigger_record:
        return failure_json(message="Trigger ID not found", status_code=S_BADREQUEST_CODE)

    triggered_at = datetime.now().replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")

    event_data = {
        "trigger_id": trigger_record["id"],
        "trigger_name": trigger_record["trigger_name"],
        "trigger_type": trigger_record.get("trigger_type", None),
        "status": trigger_record["status"],
        "triggered_at": triggered_at,
        "trigger_count": (trigger_record.get("trigger_count") or 0) + 1
    }
    response = insert_query(table_name=S_TRIGGER_EVENTS_TABLE, data=event_data)

    if response["status_bool"]:
        update_data = {
            "last_triggered_on": triggered_at,
            "trigger_count": (trigger_record.get("trigger_count") or 0) + 1
        }
        if trigger_record["interval"] is None:
            update_data["status"] = "inactive"
        else:
            trigger_time = (datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=trigger_record["interval"])).strftime("%Y-%m-%d %H:%M")
            update_data["trigger_time"] = trigger_time


        update_query(table_name=S_TRIGGER_TABLE, conditions={"id": trigger_id}, data=update_data)

        return success_json(records=response["records"], message="Trigger event logged successfully")

    return failure_json(message=f"Failed to log trigger event: {response.get('message')}",
                        status_code=S_BADREQUEST_CODE)


@router.get("/triggered_events/fetch_events")
@authorize_token
async def get_logged_events(
        request: Request,
        trigger_id: int = Query(None, description="ID of the trigger record"),
        trigger_name: str = Query(None, description="Name of your trigger"),
        trigger_type: str = Query(None, description="Type of trigger api/scheduled"),
        status: EventStatus = Query(None, description="Filter by event status (active/archived)"),
        num_records: int = Query(None, description="No of records to fetch"),
        token: HTTPAuthorizationCredentials = Depends(security)
):
    conditions = {}
    if trigger_id is not None:
        conditions["trigger_id"] = trigger_id
    if trigger_name is not None:
        conditions["trigger_name"] = trigger_name
    if status is not None:
        conditions["status"] = status.value
    if trigger_type is not None:
        conditions["trigger_type"] = trigger_type

    response = select_query(table_name=S_TRIGGER_EVENTS_TABLE, conditions=conditions, num_records=num_records)
    if response:
        return success_json(records=response, message="Fetched triggered event logs successfully")

    return failure_json(message="No Records Found", status_code=S_NOTFOUND_CODE)


@router.patch("/triggered_events/update_status")
@authorize_token
async def update_trigger_event_status(
        request: Request,
        trigger_id: int = Query(..., description="ID of the trigger event"),
        status: EventStatus = Query(..., description="New status (active/archived)"),
        token: HTTPAuthorizationCredentials = Depends(security),
):
    # Check if the trigger event exists
    existing_event = select_query(table_name=S_TRIGGER_EVENTS_TABLE, conditions={"trigger_id": trigger_id})
    if not existing_event:
        return failure_json(message="Trigger event not found", status_code=S_NOTFOUND_CODE)

    # Update only the status field
    update_response = update_query(table_name=S_TRIGGER_EVENTS_TABLE, conditions={"trigger_id": trigger_id},
                                   data={"status": status.value})[0]

    if update_response["status_bool"]:
        return success_json(message="Status updated successfully", records=update_response["records"])

    return failure_json(message="Failed to update status", status_code=S_NOTFOUND_CODE)


@router.delete("/triggered_events/delete_event")
@authorize_token
async def delete_trigger(request: Request, trigger_id: int, token: HTTPAuthorizationCredentials = Depends(security)):
    delete_response = delete_query(table_name=S_TRIGGER_EVENTS_TABLE, record_id=trigger_id)[0]
    if delete_response["status_bool"]:
        return success_json(records=[], message="Record Deleted Successfully")
    return failure_json(message=f"Cannot Delete Record, {delete_response['message']}", status_code=S_BADREQUEST_CODE)


@router.patch("/triggered_logs/update_and_delete")
async def trigger_update_and_delete(
        request: Request,
        token: HTTPAuthorizationCredentials = Depends(security),
):
    response = update_and_delete_records()
    return success_json(records=[response], message="Records updated and deleted successfully")
