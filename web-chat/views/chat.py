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
    """Gradio 화면 기록을 컨트롤러가 받는 Conversation으로 변환한다.

    답변 없이 남은 질문은 제외하고 완성된 질문·답변만 최대 6쌍 남긴다.
    첫 질문은 자기소개로 따로 보존하여 오래된 기록을 줄여도 유지한다.
    """
    def content(item):
        """문자열 또는 콘텐츠 블록 목록으로 오는 Gradio 본문에서 텍스트를 꺼낸다."""
        value = item["content"]
        if isinstance(value, str):
            return value
        return "".join(block.get("text", "") for block in value if block.get("type") == "text")

    messages = []
    pending = None
    # 실패하거나 취소한 요청은 사용자 말풍선만 남을 수 있어 답변과 짝지어 수집한다.
    for item in history:
        if item["role"] == "user":
            pending = {"role": "user", "content": content(item)}
        elif item["role"] == "assistant" and pending is not None and content(item):
            messages.extend([pending, {"role": "assistant", "content": content(item)}])
            pending = None
    return Conversation(intro=messages[0]["content"] if messages else "",
                        messages=messages[-12:])


def build_view(controller):
    """채팅 화면을 만들고 공유 URL이 설정되어 있으면 Delightex 장면을 나란히 붙인다.

    장면은 iframe으로 표시할 뿐 외부에서 제어하지 않는다.
    답변 자막은 iframe 밖의 웹 요소이며 채팅 기록 변경으로 갱신한다.
    """
    embed_url = os.getenv("DELIGHTEX_EMBED_URL", "").strip()
    if embed_url:
        # 편집 페이지나 임의 사이트 대신 공식 공유 링크만 iframe에 허용한다.
        parsed = urlsplit(embed_url)
        if (parsed.scheme != "https" or parsed.hostname != "edu.delightex.com"
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or not re.fullmatch(r"/[A-Z0-9]{3}-[A-Z0-9]{3}", parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError("DELIGHTEX_EMBED_URL must be an official https://edu.delightex.com/XXX-XXX share URL")

    async def respond(message, history):
        """화면 입력을 공통 컨트롤러에 전달하고 오류를 Gradio 알림으로 표시한다."""
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
                # 자막은 부모 웹의 요소다. 갱신 시 iframe을 다시 로드하지 않는다.
                with gr.Column(scale=7, min_width=320):
                    gr.HTML('<section data-persona-stage class="persona-stage">'
                            '<iframe class="delightex-scene" title="세종 3D 장면" '
                            f'src="{escape(embed_url, quote=True)}" '
                            'allow="fullscreen; xr-spatial-tracking" allowfullscreen '
                            'referrerpolicy="strict-origin-when-cross-origin"></iframe>'
                            '<div class="scene-caption"><strong>세종</strong>'
                            f'<p data-caption data-opening="{escape(OPENING, quote=True)}" '
                            f'aria-live="polite">{escape(OPENING)}</p></div></section>')
            with gr.Column(scale=4, min_width=320):
                chat = build_chat(respond)
        if embed_url:
            # 기록이 바뀌면 자막 텍스트만 갱신한다. iframe에는 메시지를 보내지 않는다.
            chat.chatbot.change(fn=None, inputs=[chat.chatbot], outputs=[], queue=False,
                                js=Path(__file__).with_name("caption.js").read_text(encoding="utf-8"))
    return view


def build_chat(respond):
    """입력창과 대화 목록을 구성한다. 전송·재시도·취소 동작은 Gradio가 담당한다."""
    return gr.ChatInterface(
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
