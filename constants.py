from enum import Enum
import os

# PG_HOST = os.getenv("PG_HOST")
# PG_PORT = os.getenv("PG_PORT")
# PG_USER = os.getenv("PG_USER")
# PG_PASSWORD = os.getenv("PG_PASSWORD")
# PG_DATABASE = os.getenv("PG_DATABASE")
# SENDGRID_API = os.getenv("SENDGRID_API")

PG_HOST = "dpg-cunmtk2n91rc73dqmklg-a.oregon-postgres.render.com"
PG_PORT = 5432
PG_USER = "trigger_service_user"
PG_PASSWORD = "iKP7eKkRXSNmWPYYrpeqbfGHBLtCg02u"
PG_DATABASE = "trigger_service"


TOKEN_ALGORITHM = "HS256"

# STATUS CODES
S_BADREQUEST_CODE = 400
S_NOTFOUND_CODE = 404
S_SUCCESS_CODE = 200
S_UNAUTHORIZED_CODE = 401
S_FORBIDDEN_CODE = 403
S_INTERNALERROR_CODE = 500

# TABLE NAMES
S_TRIGGER_TABLE = "ENTRY_TRIGGERS"
S_TRIGGER_EVENTS_TABLE = "TRIGGERED_EVENTS"

# CONSTRAINTS
S_NOT_NULL = "NOT NULL"
S_UNIQUE = "NOT NULL UNIQUE"


SECRET_KEY = "11923"


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Book_Status(Enum):
    RESERVED = "rented"
    RETURNED = "available"
