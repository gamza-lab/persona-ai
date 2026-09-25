from pathlib import Path
from html import escape
import os
import re
from urllib.parse import urlsplit

import gradio as gr
from fastapi import HTTPException
from pydantic import ValidationError

from app import OPENING
from models.conversation import ChatRequest, Conversation


def conversation_from_history(history):
    def content(item):
        value = item["content"]
        if isinstance(value, str):
            return value
        return "".join(block.get("text", "") for block in value if block.get("type") == "text")

    messages = []
    pending = None
    # Failed/cancelled submissions may leave an unanswered user bubble in Gradio.
    for item in history:
        if item["role"] == "user":
            pending = {"role": "user", "content": content(item)}
        elif item["role"] == "assistant" and pending is not None and content(item):
            messages.extend([pending, {"role": "assistant", "content": content(item)}])
            pending = None
    return Conversation(intro=messages[0]["content"] if messages else "",
                        messages=messages[-12:])


def build_view(controller):
    embed_url = os.getenv("DELIGHTEX_EMBED_URL", "").strip()
    if embed_url:
        parsed = urlsplit(embed_url)
        if (parsed.scheme != "https" or parsed.hostname != "edu.delightex.com"
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or not re.fullmatch(r"/[A-Z0-9]{3}-[A-Z0-9]{3}", parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError("DELIGHTEX_EMBED_URL must be an official https://edu.delightex.com/XXX-XXX share URL")

    async def respond(message, history):
        try:
            state = conversation_from_history(history)
            result = await controller.chat(ChatRequest(message=message, state=state))
            return result.reply
        except ValidationError:
            raise gr.Error("메시지는 1~500자로 입력해 주세요.")
        except HTTPException as error:
            raise gr.Error(error.detail)

    with gr.Blocks(title="세종과의 만남", analytics_enabled=False, fill_height=True, fill_width=True) as view:
        gr.HTML('<header class="persona-header"><div class="seal">世宗</div>'
                '<div><p>1449 · 조선</p><h1>세종과의 만남</h1></div>'
                '<span class="fiction">AI 역사 인물 · 창작 대화</span></header>')
        with gr.Row(elem_classes=["experience-layout"]):
            if embed_url:
                with gr.Column(scale=7, min_width=320):
                    gr.HTML('<section data-persona-stage class="persona-stage">'
                            '<iframe class="delightex-scene" title="세종 3D 장면" '
                            f'src="{escape(embed_url, quote=True)}" '
                            'allow="fullscreen; xr-spatial-tracking" allowfullscreen '
                            'referrerpolicy="strict-origin-when-cross-origin"></iframe>'
                            '<div class="scene-caption"><strong>세종</strong>'
                            f'<p data-caption aria-live="polite">{escape(OPENING)}</p></div>'
                            '<div class="scene-audio"><label><input type="checkbox" data-voice> 음성</label>'
                            '<button type="button" data-replay>다시 듣기</button>'
                            '<button type="button" data-stop>음성 중지</button>'
                            '<span data-audio-status role="status"></span></div></section>',
                            js_on_load=Path(__file__).with_name("scene.js").read_text(encoding="utf-8"))
            with gr.Column(scale=4, min_width=320):
                build_chat(respond)
    return view


def build_chat(respond):
    chat = gr.ChatInterface(
            fn=respond,
            chatbot=gr.Chatbot(label="세종", placeholder=OPENING, height="65vh",
                               buttons=["copy"], allow_tags=False,
                               avatar_images=(None, str(Path(__file__).with_name("sejong.webp")))),
            textbox=gr.Textbox(placeholder="전하께 말을 건네 보세요", max_lines=5,
                               label="메시지", show_label=False,
                               max_length=500, submit_btn=True, stop_btn=True),
            flagging_mode="never", save_history=False, api_visibility="private",
            concurrency_limit=4, stop_btn=True, fill_width=True,
        )
    chat.chatbot.change(fn=None, inputs=[chat.chatbot], outputs=[], queue=False,
                        js=Path(__file__).with_name("caption.js").read_text(encoding="utf-8"))
