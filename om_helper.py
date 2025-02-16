import re

import pytz

from constants import SECRET_KEY, TOKEN_ALGORITHM

from jose import jwt, JWTError
from datetime import datetime, timedelta
from functools import wraps
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer


def current_time():
    ist = pytz.timezone('Asia/Kolkata')
    date = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S.%f')
    return date


def parse_timestamp(str_timestamp: str = None, dt_timestamp: datetime = None):
    format = "%Y-%m-%d %H:%M:%S.%f"

    if dt_timestamp:
        return dt_timestamp.strftime(format=format)
    elif str_timestamp:
        try:
            print("HELLO")
            return datetime.strptime(str_timestamp, format)
        except ValueError:
            print("BYE")
            return None  # Return None for invalid format

    return None


def success_json(records: list, message: str = ""):
    return JSONResponse(content={"status": "success", "status_code":200, "message": message, "timestamp": current_time(),
                                 "count": len(records),
                                 "records": records, "status_bool": True}, status_code=200)


def failure_json(message: str, status_code: int):
    return JSONResponse(content={"status": "failure", "status_code":status_code, "message": message, "timestamp": current_time(),
                                 "count": 0, "records": [], "status_bool": False}, status_code=status_code)


def create_access_token(user_id: int, meta_data=None, expires_time: int = None) -> str:
    if expires_time == -1:
        expire = datetime.utcnow() + timedelta(minutes=1440 * 365 * 10)
    elif expires_time:
        expire = datetime.utcnow() + timedelta(minutes=expires_time)
    else:
        expire = datetime.utcnow() + timedelta(minutes=1440 * 7)
    to_encode = {"user_id": user_id}
    if meta_data:
        to_encode["meta_data"] = meta_data
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=TOKEN_ALGORITHM)
    return encoded_jwt


def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        return {"validity": True, "payload": payload}
    except JWTError:
        raise JWTError("Token is invalid or expired")


security = HTTPBearer()


def authorize_token(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        token = None
        if 'token' in kwargs:
            token = kwargs.get('token')

        if token:
            try:
                if validate_token(token=token.credentials):
                    print()
                else:
                    raise JWTError("Token is invalid or expired")
            except JWTError:
                return JSONResponse(
                    content={"status": "failure", "message": "not authorized"},
                    status_code=401
                )

        return await func(request, *args, **kwargs)

    return wrapper


def validate_user_fields(user_details):
    phone = user_details.get("user_phone")
    name = user_details.get("user_name")
    email = user_details.get("user_email")
    password = user_details.get("user_password")

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{10,}$'

    if phone is not None:
        if not phone.isdigit():
            return 'Phone number must contain only digits'
        elif len(phone) != 10:
            return 'Phone number must be exactly 10 digits'

    if name is not None:
        stripped_name = name.strip()
        if len(stripped_name) < 3:
            return 'Name must have at least 3 characters'
        elif not re.match("^[a-zA-Z\s]+$", stripped_name):
            return 'Name must not contain special characters'

    if email is not None:
        if not re.match(email_regex, email):
            return 'Invalid email format'

    if password is not None:
        if not re.match(password_regex, password):
            return 'Password must be at least 10 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character'

    return None
