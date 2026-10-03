# 세종 페르소나 AI 실습

VESSL에서 실행하는 하나의 언어 모델 서버를 CLI, 웹 브라우저, Roblox Studio에서
각각 사용할 수 있는 실습 프로젝트입니다.

## 실습 선택

- CLI 대화: 저장소 루트의 `app.py`
- 웹 브라우저 채팅: [`web-chat/README.md`](web-chat/README.md)
- Roblox 채팅: [`roblox-chat/README.md`](roblox-chat/README.md)
- Roblox Studio 프로젝트: [`SejongAI.rbxlx`](roblox-chat/SejongAI/SejongAI.rbxlx)

## 공통 실행 환경

VESSL Workspace는 `Torch 2.9.1 (CUDA 13.0.1, Python 3.13)` 컨테이너와
`A100 SXM 80GB x 1` GPU를 사용합니다. 웹과 Roblox 실습은 외부 접속을 위해
각 안내서에 적힌 HTTP 포트도 추가해야 합니다.

## 저장소 구조

```text
app.py                    # 터미널용 대화 프로그램
web-chat/                 # 웹 채팅 서버와 화면
roblox-chat/
  SejongAI/               # Roblox Studio 프로젝트와 Luau 코드
  vessl-server/           # Roblox용 Python API 서버
```

설치, 서버 실행, 외부 주소 연결 방법은 선택한 실습의 README를 따릅니다.
