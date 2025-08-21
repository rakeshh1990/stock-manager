from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Notifier Service")

class NotifyIn(BaseModel):
    user_id: int
    channel: str = "email"
    message: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "notifier"}

@app.post("/notify")
def notify(payload: NotifyIn):
    # Stub: log and pretend we sent it
    return {"status": "queued", "to_user": payload.user_id, "channel": payload.channel}
