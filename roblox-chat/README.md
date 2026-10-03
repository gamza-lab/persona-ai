# 세종AI Roblox 실습

VESSL 서버에서 세종 페르소나 모델과 Roblox용 API를 실행하고, 개인 PC의 Roblox Studio에서 서버 주소를 연결하는 실습입니다.

## 전체 순서

1. VESSL Workspace를 만든다.
2. VESSL 터미널에서 프로젝트와 패키지를 설치한다.
3. VESSL 터미널 두 개에서 모델 서버와 Roblox 채팅 서버를 실행한다.
4. 개인 PC에 Roblox 프로젝트를 내려받는다.
5. Roblox Studio에 VESSL 주소를 입력하고 실행한다.

# 서버 설정: VESSL

## 1. Workspace 만들기

VESSL의 **Workspaces** 화면에서 새 Workspace를 만들고 다음 값을 선택합니다.

| 항목 | 선택할 값 |
| --- | --- |
| Container | `Torch 2.9.1 (CUDA 13.0.1, Python 3.13)` |
| GPU | `A100 SXM 80GB x 1` |
| Persistent volume | 사용할 Cluster storage 볼륨 |
| Mount Path | `/root` |

**Advanced settings**에서 **Add port**를 눌러 다음 포트를 추가합니다.

| 종류 | 포트 | 이름 |
| --- | --- | --- |
| HTTP | `7860` | `roblox-chat` |

Workspace를 시작한 뒤 **JupyterLab**을 엽니다.

## 2. 프로젝트 설치하기

JupyterLab의 Launcher에서 **Terminal**을 엽니다. GPU가 올바르게 연결되었는지 확인합니다.

```bash
nvidia-smi
```

프로젝트를 `/root`에 내려받습니다.

```bash
cd /root
git clone --depth 1 --branch feature/roblox-chat https://github.com/gamza-lab/persona-ai.git
cd persona-ai
```

이미 `/root/persona-ai`가 있다면 새로 복제하지 않고 다음 명령으로 업데이트합니다.

```bash
cd /root/persona-ai
git fetch origin feature/roblox-chat
git switch feature/roblox-chat
git pull --ff-only origin feature/roblox-chat
```

Python 3.13 가상환경과 필요한 패키지를 설치합니다. 최초 한 번만 실행하면 됩니다.
모델 서버와 Roblox API 서버는 같은 가상환경을 사용합니다.

```bash
cd /root/persona-ai
python3.13 --version
python3.13 -m venv .venv
.venv/bin/python -m pip install -r roblox-chat/vessl-server/requirements.txt
```

다음 명령이 `Python 3.13.x`를 표시해야 합니다.

```bash
.venv/bin/python --version
```

`/root`에 Persistent volume을 연결했으므로 프로젝트, 가상환경과 다운로드한 모델은 Workspace를 다시 시작해도 유지됩니다.

## 3. 터미널 1에서 모델 서버 실행하기

첫 번째 터미널에서 다음 명령을 실행합니다.

```bash
cd /root/persona-ai
source .venv/bin/activate

vllm serve Qwen/Qwen3.5-27B-FP8 \
  --host 127.0.0.1 \
  --port 8000 \
  --language-model-only \
  --max-model-len 8192 \
  --max-num-seqs 1 \
  --gpu-memory-utilization 0.90 \
  --enforce-eager
```

처음 실행할 때는 약 31GB의 모델을 다운로드합니다. `Application startup complete`가 표시될 때까지 기다리고, 이 터미널은 계속 실행해 둡니다.

## 4. 터미널 2에서 Roblox 채팅 서버 실행하기

JupyterLab에서 새 Terminal을 하나 더 엽니다. 먼저 모델 서버가 준비되었는지 확인합니다.

```bash
cd /root/persona-ai
source .venv/bin/activate
curl -fsS http://127.0.0.1:8000/v1/models
```

결과에 `Qwen/Qwen3.5-27B-FP8`이 표시되면 Roblox 채팅 서버를 실행합니다.

```bash
WEB_HOST=0.0.0.0 WEB_PORT=7860 python roblox-chat/vessl-server/server.py
```

이 터미널도 실습이 끝날 때까지 실행해 둡니다.

## 5. 서버 주소 확인하기

1. VESSL Workspace에서 **Connect**를 누릅니다.
2. **Exposed services**에서 `roblox-chat`을 찾습니다.
3. 표시된 `https://...` 주소를 복사합니다.
4. 주소 뒤에 `/ready`를 붙여 브라우저에서 엽니다.
5. `{"ready": true}`가 표시되면 서버 준비가 끝난 것입니다.

# 클라이언트 설정: 개인 PC

## 1. Roblox 프로젝트 다운로드하기

1. GitHub에서 [`SejongAI.rbxlx`](./SejongAI.rbxlx)를 엽니다.
2. 오른쪽 위의 **Download raw file**을 눌러 개인 PC에 내려받습니다.
3. Roblox Studio를 실행합니다.
4. **파일 > 파일에서 열기**를 누르고 `SejongAI.rbxlx`를 선택합니다.
5. **파일 > Roblox에 다른 이름으로 게시**를 눌러 자신의 계정에 저장합니다.

## 2. HTTP 요청 허용하기

Roblox Studio 위쪽의 **홈 > 게임 설정 > 보안**을 열고 **HTTP 요청 허용**을 켠 뒤 저장합니다.

## 3. VESSL 주소 입력하기

1. Roblox Studio의 **보기** 메뉴에서 **탐색기**와 **속성**을 엽니다.
2. **탐색기 > ServerScriptService > PersonaChatServer**를 선택합니다.
3. **속성(Attributes)**에서 `PersonaApiUrl`을 찾습니다.
4. `https://replace-me.invalid`을 지우고 VESSL에서 복사한 주소를 붙여넣습니다.

주소 끝에 `/ready`, `/api/chat` 또는 `/`를 추가하지 않습니다.

```text
올바른 예: https://roblox-chat-내-워크스페이스.cloud.vessl.ai
잘못된 예: https://roblox-chat-내-워크스페이스.cloud.vessl.ai/api/chat
```

## 4. 실행하기

1. Roblox Studio 위쪽의 **Play**를 누릅니다.
2. 화면 아래 입력칸에 질문을 입력합니다.
3. **보내기**를 누릅니다.
4. 세종 캐릭터 위에 답변 말풍선이 나타나면 성공입니다.

# 실습 종료

1. VESSL의 터미널 2에서 `Ctrl+C`를 눌러 Roblox 채팅 서버를 종료합니다.
2. 터미널 1에서 `Ctrl+C`를 눌러 모델 서버를 종료합니다.
3. VESSL Workspace를 **Stop**합니다. 브라우저만 닫으면 GPU 사용이 종료되지 않습니다.

# 문제가 생겼을 때

| 문제 | 확인할 것 |
| --- | --- |
| `persona-ai` 폴더가 이미 있다는 메시지 | 새로 복제하지 말고 기존 프로젝트 업데이트 명령 사용 |
| `/ready`에서 `false` 표시 | 모델 서버가 `Application startup complete` 상태인지 확인 |
| 서버 주소 설정 메시지 | `PersonaApiUrl`에 기본 주소를 입력했는지 확인 |
| HTTP 요청 오류 | Roblox Studio에서 **HTTP 요청 허용**을 켰는지 확인 |
| 첫 실행이 오래 걸림 | 모델 다운로드가 끝날 때까지 기다린 뒤 다시 확인 |
