from fastapi import FastAPI
from pydantic import BaseModel
# from fastapi.middleware.cors import CORSMiddleware;
from fastapi.responses import StreamingResponse

import os



from api.chatbot.engine import getChatbotResponse



class incomingMessage(BaseModel):
    message: str
    sessionId: str


app=FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],     
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.post("/api")
def root(item:  incomingMessage):
    message = item.message
    sessionId = item.sessionId
    print(sessionId)
    tokenGenerator = getChatbotResponse(message, sessionId)
    return StreamingResponse(tokenGenerator, media_type="text/plain")





from fastapi import Request
@app.post("/debug")
async def debug(request: Request):
    body = await request.json()
    print("Raw body:", body)
    return body
