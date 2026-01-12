
from fastapi import APIRouter
import firebase_admin
from firebase_admin import credentials, messaging

router = APIRouter()

cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

@router.post("/send")
def send_push(token: str, title: str, body: str):
    msg = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
    )
    messaging.send(msg)
    return {"status": "sent"}
