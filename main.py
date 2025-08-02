from fastapi import FastAPI
from pydantic import BaseModel
from portfolio_agent.agent import PortfolioAssistant

app = FastAPI()
assistant = PortfolioAssistant()

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat(req: ChatRequest):
    response = assistant.chat(req.message, req.history)
    return {"response": response}
