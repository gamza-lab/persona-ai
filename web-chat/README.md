# 세종 웹 채팅 실습

VESSL에서 EXAONE 모델과 웹 서버를 실행하고 브라우저로 세종 페르소나와 대화하는 실습입니다.

## 1. Workspace 만들기

VESSL Workspace를 다음 옵션으로 생성합니다.

| 항목 | 선택할 값 |
| --- | --- |
| Container | `Torch 2.9.1 (CUDA 13.0.1, Python 3.13)` |
| GPU | `A100 SXM 80GB x 1` |
| HTTP port | `7860` |
| Port name | `web-chat` |

## 2. 프로젝트 설치하기

```bash
cd /root
git clone --depth 1 https://github.com/gamza-lab/persona-ai.git
cd persona-ai
python3.13 -m venv .venv
.venv/bin/python -m pip install -r web-chat/requirements.txt
```

## 3. 터미널 1에서 모델 서버 실행하기

```bash
cd /root/persona-ai
source .venv/bin/activate

vllm serve LGAI-EXAONE/EXAONE-4.5-33B \
  --host 127.0.0.1 \
  --port 8000 \
  --language-model-only \
  --max-model-len 8192 \
  --max-num-seqs 1 \
  --gpu-memory-utilization 0.90 \
  --enforce-eager
```

`Application startup complete`가 표시될 때까지 기다리고 이 터미널은 계속 실행해 둡니다.

## 4. 터미널 2에서 웹 서버 실행하기

```bash
cd /root/persona-ai
source .venv/bin/activate
curl -fsS http://127.0.0.1:8000/v1/models
WEB_HOST=0.0.0.0 WEB_PORT=7860 python web-chat/server.py
```

VESSL의 **Connect > Exposed services**에서 `web-chat` 주소를 열면 됩니다.
모델 준비 여부는 외부 주소 뒤에 `/ready`를 붙여 확인할 수 있습니다.

## 설정

모델 서버는 기본적으로 `http://127.0.0.1:8000/v1`을 사용합니다.
필요하면 `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY`, `WEB_HOST`,
`WEB_PORT`, `CORS_ORIGINS` 환경변수로 변경할 수 있습니다.

## API

- `GET /health`: 웹 서버 생존 확인
- `GET /ready`: 모델 연결 준비 여부 확인
- `POST /api/chat`: 메시지와 대화 상태를 전달해 답변 생성

## 폴더 구조

```text
web-chat/
  server.py               # 서버 시작
  models/conversation.py  # 대화 데이터
  models/persona.py       # 세종 자료 검색과 모델 호출
  controllers/chat.py     # 질문과 답변 처리
  views/chat.py           # 웹 화면
  views/style.css         # 화면 스타일
  views/sejong.webp       # 세종 초상 이미지
```
