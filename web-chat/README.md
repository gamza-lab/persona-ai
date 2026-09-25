# 세종 웹 채팅

기존 CLI를 변경하지 않고 같은 프롬프트, BM25 검색, `data.json`을 재사용합니다.
Gradio 화면과 FastAPI JSON API가 하나의 컨트롤러를 사용합니다.

## 구조

```text
web-chat/
  server.py               # 서버 조립, 수명 주기, HTTP 라우팅
  models/conversation.py  # 요청, 응답, 대화 상태 검증
  models/persona.py       # 기존 페르소나와 vLLM 연결
  controllers/chat.py     # 대화 처리, 동시성, 오류 처리
  views/chat.py           # Gradio 화면
  views/style.css
```

## 실행

저장소 루트에서 Python 3.12 환경을 사용합니다.

```bash
python -m pip install -r web-chat/requirements.txt
python web-chat/server.py
```

기본 웹 주소는 `http://127.0.0.1:7860`입니다. 모델은 별도로
`http://127.0.0.1:8000/v1`에서 실행되어야 합니다.
`MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY`, `WEB_HOST`, `WEB_PORT`,
`CORS_ORIGINS`(쉼표 구분)으로 변경합니다. 환경변수는 실행 전에 설정하며
`.env` 파일을 자동으로 읽지는 않습니다.

## VESSL

생성한 워크스페이스: `persona-ai-3` (`wsp-fxfdhedhygbk`).
외부 주소: https://web-chat-wsp-fxfdhedhygbk.betelgeuse.cloud.vessl.ai/

포트는 워크스페이스 생성 명령의 `--port web-chat:7860:http`로 자동 등록했습니다.
컨테이너에서 7860을 열기만 해서는 외부 경로가 생기지 않습니다.
8000 모델 포트는 외부에 노출하지 않습니다.

### 최초 설치

VESSL Linux 터미널에서 실행합니다. 저장소가 `/root/persona-ai`에 있고,
기본 이미지의 Python이 `/opt/conda/bin/python`에 있는 환경 기준입니다.
이미 설치된 환경에서는 이 단계를 건너뜁니다. 모델과 웹의 의존성은 별도 환경에 설치합니다.

```bash
cd /root/persona-ai
/opt/conda/bin/python -m pip install 'uv==0.10.12'
/opt/conda/bin/python -m uv python install 3.12
/opt/conda/bin/python -m uv venv .venv-model --python 3.12
/opt/conda/bin/python -m uv pip install --python .venv-model/bin/python 'vllm==0.29.0'
/opt/conda/bin/python -m uv venv .venv-web --python 3.12
/opt/conda/bin/python -m uv pip install --python .venv-web/bin/python -r web-chat/requirements.txt
```

### 모델 실행: 터미널 1

가상환경을 활성화해야 vLLM이 `ninja` 등의 빌드 도구도 찾을 수 있습니다.
최초 실행에는 모델 다운로드와 초기화 시간이 필요합니다.

```bash
cd /root/persona-ai
source .venv-model/bin/activate
vllm serve Qwen/Qwen3.5-27B-FP8 \
  --host 127.0.0.1 --port 8000 \
  --language-model-only --max-model-len 8192 --max-num-seqs 1 \
  --gpu-memory-utilization 0.90 --enforce-eager
```

### 웹 실행: 터미널 2

```bash
cd /root/persona-ai
WEB_HOST=0.0.0.0 .venv-web/bin/python web-chat/server.py
```

두 터미널을 유지한 상태에서 위 외부 주소에 접속합니다. 모델 준비 여부는
외부 주소의 `/ready`에서 확인할 수 있습니다. 각 프로세스는 해당 터미널에서 `Ctrl+C`로 종료합니다.
이미 모델이나 웹 서버가 실행 중이면 같은 포트로 중복 실행하지 마세요.

위 명령은 포그라운드 실행이며 로그는 각 터미널에 출력됩니다. 워크스페이스를
재시작한 뒤에는 설치를 반복하지 않고 모델과 웹 실행 단계만 수행합니다.
앞서 구성한 테스트용 백그라운드 배포의 로그는 `/tmp/persona-model.log`, `/tmp/persona-web.log`에 있습니다.
A100 실행 비용이 계속 발생하므로 테스트 후 VESSL에서 워크스페이스를 일시정지하세요.

## API

- `GET /health`: 웹 서버 생존 확인.
- `GET /ready`: 모델 연결 가능 여부, 준비 전에는 503.
- `POST /api/chat`: `{ "message": "저는 민수입니다." }`.
- 응답: `{ "reply": "...", "state": { "intro": "...", "messages": [...] } }`.
- 다음 요청에 응답의 `state`를 그대로 포함하면 대화가 이어집니다.
- 새 대화는 `state`를 생략합니다. 서버에 사용자 대화 DB를 만들지 않습니다.
- 첫 발언과 최근 6회 대화를 반환합니다. 긴 대화는 모델 입력에서 오래된 쌍부터
  제외해 최근 기록 2,000자 이내로 유지합니다.
- 사용자 메시지 최대 500자. 잘못된 요청 422, 혼잡 429, 모델 오류 503, 시간 초과 504.

기본 CORS 허용 출처는 `https://edu.delightex.com`입니다.
CORS는 인증 수단이 아닙니다. 현재 데모는 인증 없이 접속할 수 있으므로 민감한 정보를
입력하지 마세요. 장기 공개 운영 전에는 인증, 호출 제한, 운영 모니터링이 필요합니다.
Gradio 대화 저장과 실행 기록은 비활성화했습니다.

## Delightex Edu

외부 HTTPS와 CORS 사전 요청 검증은 성공했지만, Edu 장면 내부 `fetch` 사용 가능 여부는
아직 확인하지 못했습니다. 타입 선언만으로 런타임 네트워크 기능이 생기지는 않습니다.
프로젝트 로그인 후 장면에서 검증해야 포팅 가능 여부를 확정할 수 있습니다.

초상 이미지는 사용자가 지정한 원본을 `views/sejong.webp`에 보관합니다.
출처: [사용자 제공 이미지](https://i.namu.wiki/i/NoJSCwwjqsqwMongIdteq4u_NEqe8M2Gx5OXl_soI6axeLqpnfCwctoW5BWaKrq9LKECbYLhNxsEq504VmR7olICNq2bH8HU08w5u4FCcKcHdl1ykERQTjyFhfTLg56f4wNIcL54CxeEx_lCLtIErIbFIs5uiFkw9nGdtozKQ9c.webp).
