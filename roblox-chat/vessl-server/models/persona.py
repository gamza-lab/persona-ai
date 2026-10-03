import os

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app import BASE_URL, MODEL_NAME, SYSTEM_PROMPT, make_retriever, tokenize
from models.conversation import ChatRequest


class PersonaModel:
    """기존 세종 프롬프트와 역사 자료 검색을 재사용해 vLLM에 답변을 요청한다."""

    def __init__(self):
        """검색기와 모델 클라이언트를 만들고 프롬프트→모델→문자열 처리를 연결한다."""
        self.base_url = os.getenv("MODEL_BASE_URL", BASE_URL).rstrip("/")
        self.retriever = make_retriever()
        self.llm = ChatOpenAI(
            base_url=self.base_url, model=os.getenv("MODEL_NAME", MODEL_NAME),
            api_key=os.getenv("MODEL_API_KEY", "EMPTY"), max_tokens=400,
            temperature=0.2, seed=42, max_retries=0, timeout=90,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT), MessagesPlaceholder("history"),
            ("human", "{question}"),
        ])
        self.chain = prompt | self.llm | StrOutputParser()

    def inputs(self, request: ChatRequest):
        """현재 질문, 이전 대화, 검색한 역사 근거를 프롬프트 입력으로 구성한다.

        사용자 자기소개는 따로 보존하고, 모델에 넣는 이전 대화 본문은
        2,000자 이내가 되도록 오래된 질문·답변 쌍부터 제외한다.
        """
        messages = request.state.messages
        previous = messages[-2].content if messages else ""
        # 짧은 후속 질문은 직전 질문으로 보완하고 현재 질문에 검색 가중치를 준다.
        query = f"{request.message} {request.message} {previous}"
        scores = self.retriever.vectorizer.get_scores(tokenize(query))
        # 키워드가 전혀 겹치지 않는 상위 문서를 근거로 넣지 않는다.
        evidence = [doc.metadata["evidence"] for doc in self.retriever.invoke(query)
                    if scores[doc.metadata["index"]] > 0]
        history = list(messages)
        # 원본 상태는 바꾸지 않고 모델에 보낼 기록만 쌍 단위로 줄인다.
        while history and sum(len(item.content) for item in history) > 2000:
            history = history[2:]
        return {
            "intro": request.state.intro or request.message,
            "question": request.message,
            "history": [(item.role, item.content) for item in history],
            "evidence": "\n\n".join(evidence) or "관련 역사 자료가 검색되지 않았다.",
        }

    async def respond(self, request: ChatRequest):
        """준비한 입력으로 비동기 추론을 실행하고 답변 문자열을 반환한다."""
        return (await self.chain.ainvoke(self.inputs(request))).strip()

    async def ready(self):
        """모델 목록 API 응답을 확인한다. 실제 답변 생성까지 검사하는 것은 아니다."""
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {os.getenv('MODEL_API_KEY', 'EMPTY')}"},
                )
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self):
        """앱 종료 시 비동기·동기 모델 클라이언트의 연결을 모두 닫는다."""
        await self.llm.root_async_client.close()
        self.llm.root_client.close()
