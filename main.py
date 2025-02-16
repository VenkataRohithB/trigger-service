import uvicorn

from fastapi import FastAPI
from route_trigger import router as trigger_router
from route_triggerlogs import router as events_router
from route_common import router as auth_router
app = FastAPI(
    title="Trigger Service"
)

app.include_router(trigger_router, tags=["trigger"])
app.include_router(events_router, tags=["trigger_events"])
app.include_router(auth_router, tags=["auth"])

uvicorn.run(app=app, host="0.0.0.0", port=8989)
