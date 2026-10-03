# 세종 페르소나 CLI 실습

VESSL에서 EXAONE 모델 서버를 실행하고 터미널에서 세종 페르소나와 대화하는 기본 실습입니다.
이 폴더의 프롬프트와 역사 자료는 웹 및 Roblox 채팅 실습에서도 공통으로 사용합니다.

## 폴더 구조

```text
persona-core/
  app.py       # 터미널 대화 프로그램과 공통 페르소나 로직
  data.json    # 검색에 사용하는 세종대왕 역사 자료
```

## 1. Workspace 만들기

VESSL Workspace를 다음 옵션으로 생성합니다.

| 항목 | 선택할 값 |
| --- | --- |
| Container | `Torch 2.9.1 (CUDA 13.0.1, Python 3.13)` |
| GPU | `A100 SXM 80GB x 1` |

## 2. 프로젝트 설치하기

```bash
cd /root
git clone --depth 1 https://github.com/gamza-lab/persona-ai.git
cd persona-ai
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
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

## 4. 터미널 2에서 CLI 실행하기

```bash
cd /root/persona-ai
source .venv/bin/activate
curl -fsS http://127.0.0.1:8000/v1/models
python persona-core/app.py
```

대화를 마치려면 `Ctrl+C`를 누릅니다. 이후 모델 서버도 종료하고 VESSL Workspace를 중지합니다.
