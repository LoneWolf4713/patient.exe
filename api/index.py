from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from api.chatbot.engine import getChatbotResponse

class incomingMessage(BaseModel):
    message: str
    sessionId: str

app=FastAPI()

@app.post("/api")
def root(item:  incomingMessage):
    message = item.message
    sessionId = item.sessionId
    print(sessionId)
    tokenGenerator = getChatbotResponse(message, sessionId)
    return StreamingResponse(tokenGenerator, media_type="text/plain")
