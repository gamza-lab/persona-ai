import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers.chat import ChatController
from models.conversation import ChatReply, ChatRequest
from models.persona import PersonaModel
from views.chat import build_view


def create_app(model=None, with_ui=True):
    model = model if model is not None else PersonaModel()
    controller = ChatController(model)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await model.close()

    application = FastAPI(title="Persona Chat", lifespan=lifespan)
    origins = os.getenv("CORS_ORIGINS", "https://edu.delightex.com").split(",")
    application.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in origins],
                               allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @application.get("/health")
    async def health():
        return {"ok": True, "service": "persona-web-chat"}

    @application.get("/ready")
    async def ready():
        ok = await model.ready()
        return JSONResponse({"ready": ok}, status_code=200 if ok else 503)

    @application.post("/api/chat", response_model=ChatReply)
    async def chat(request: ChatRequest):
        return await controller.chat(request)

    if with_ui:
        application = gr.mount_gradio_app(
            application, build_view(controller), path="/", footer_links=[],
            run_history=False, show_error=False, ssr_mode=False,
            theme=gr.themes.Default(primary_hue="emerald", neutral_hue="gray",
                                    font=["Arial", "sans-serif"], font_mono=["monospace"]),
            css_paths=ROOT / "views" / "style.css",
        )
    return application


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host=os.getenv("WEB_HOST", "127.0.0.1"),
                port=int(os.getenv("WEB_PORT", "7860")))
