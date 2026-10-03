"""Roblox가 호출할 JSON API 서버를 실행한다."""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# 기존 CLI의 프롬프트와 검색 함수를 재사용할 수 있도록 저장소 루트를 등록한다.
sys.path.insert(0, str(ROOT.parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers.chat import ChatController
from models.conversation import ChatReply, ChatRequest
from models.persona import PersonaModel


def create_app(model=None):
    """Roblox용 API 앱을 구성한다."""
    model = model if model is not None else PersonaModel()
    controller = ChatController(model)

    @asynccontextmanager
    async def lifespan(app):
        """앱이 종료될 때 모델 통신에 사용한 HTTP 연결을 정리한다."""
        yield
        await model.close()

    application = FastAPI(title="Persona Chat", lifespan=lifespan)
    origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",")
               if origin.strip()]
    # 브라우저 연동이 필요한 배포에서만 허용할 출처를 명시한다. Roblox 서버 요청에는 CORS가 적용되지 않는다.
    if origins:
        application.add_middleware(CORSMiddleware, allow_origins=origins,
                                   allow_methods=["GET", "POST"],
                                   allow_headers=["Content-Type"])

    @application.get("/health")
    async def health():
        """웹 서버가 살아 있는지 확인한다. 모델 준비 여부와는 별개다."""
        return {"ok": True, "service": "persona-roblox-chat"}

    @application.get("/ready")
    async def ready():
        """모델 서버에 접근 가능한지 확인하고, 준비되지 않았으면 503을 반환한다."""
        ok = await model.ready()
        return JSONResponse({"ready": ok}, status_code=200 if ok else 503)

    @application.post("/api/chat", response_model=ChatReply)
    async def chat(request: ChatRequest):
        """질문과 이전 대화 상태를 받아 답변 및 갱신된 상태를 JSON으로 반환한다."""
        return await controller.chat(request)

    return application


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host=os.getenv("WEB_HOST", "127.0.0.1"),
                port=int(os.getenv("WEB_PORT", "7860")))
