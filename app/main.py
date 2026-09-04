from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .services import ConversationService


app = FastAPI(
    title="Northstar One AI Sales Assistant",
    version="1.0.0",
)

service = ConversationService()

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=1)


@app.get("/")
async def home():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "ai": "gemini"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        return await service.chat(
            request.session_id,
            request.message.strip(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {str(exc)}",
        )


@app.post("/api/reset")
async def reset(request: ResetRequest):
    service.reset(request.session_id)
    return {"success": True}


@app.get("/api/analytics/{session_id}")
async def analytics(session_id: str):
    try:
        return await service.analytics(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
