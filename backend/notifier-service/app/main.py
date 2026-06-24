import logging
import os
import threading
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from kafka import KafkaConsumer, TopicPartition
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("notifier-service")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC = os.getenv("KAFKA_ALERT_TOPIC", "alert.triggered")
KAFKA_GROUP_ID = os.getenv("KAFKA_NOTIFIER_GROUP", "notifier-service")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8004")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "development-internal-key")

_stop = threading.Event()
_thread: threading.Thread | None = None
_state = {"running": False, "processed": 0, "failed": 0, "last_error": None}


def _record_notification(event: dict) -> None:
    payload = {
        "event_id": event["event_id"],
        "triggered_value": event.get("triggered_value"),
        "message": event["message"],
        "priority": event.get("priority", "normal"),
    }
    response = httpx.post(
        f"{USER_SERVICE_URL}/internal/alerts/{event['alert_id']}/fired",
        json=payload,
        headers={"X-Internal-Key": INTERNAL_API_KEY},
        timeout=15,
    )
    response.raise_for_status()


def _consume() -> None:
    _state["running"] = True
    consumer = None
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value: __import__("json").loads(value.decode("utf-8")),
            consumer_timeout_ms=1000,
        )
        logger.info("Consuming topic %s from %s", KAFKA_TOPIC, KAFKA_BROKER)
        while not _stop.is_set():
            records = consumer.poll(timeout_ms=1000, max_records=20)
            for messages in records.values():
                for message in messages:
                    try:
                        event = message.value
                        if event.get("event_type") != "alert.triggered":
                            logger.warning("Ignoring unsupported event: %s", event.get("event_type"))
                        else:
                            _record_notification(event)
                            _state["processed"] += 1
                            logger.info(
                                "Recorded notification event=%s alert=%s user=%s",
                                event.get("event_id"),
                                event.get("alert_id"),
                                event.get("user_id"),
                            )
                        consumer.commit()
                    except Exception as exc:
                        _state["failed"] += 1
                        _state["last_error"] = str(exc)
                        logger.exception("Notification event processing failed")
                        # Rewind this partition so the same event is retried.
                        consumer.seek(
                            TopicPartition(message.topic, message.partition),
                            message.offset,
                        )
                        _stop.wait(2)
                        break
    except Exception as exc:
        _state["last_error"] = str(exc)
        logger.exception("Kafka consumer stopped unexpectedly")
    finally:
        _state["running"] = False
        if consumer is not None:
            consumer.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _thread
    _stop.clear()
    _thread = threading.Thread(target=_consume, name="kafka-alert-consumer", daemon=True)
    _thread.start()
    yield
    _stop.set()
    if _thread:
        _thread.join(timeout=10)


app = FastAPI(title="Notifier Service", version="2.0.0", lifespan=lifespan)

class NotifyIn(BaseModel):
    user_id: int
    channel: str = "in-app"
    message: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "notifier", "consumer": _state}

@app.post("/notify")
def notify(payload: NotifyIn):
    logger.info("Manual notification user=%s channel=%s: %s", payload.user_id, payload.channel, payload.message)
    return {"status": "accepted", "to_user": payload.user_id, "channel": payload.channel}
