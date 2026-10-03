# 세종 웹 채팅 서버

Roblox `세종AI`가 사용할 VESSL 서버입니다.

실습자는 서버 구조를 이해하거나 터미널에서 명령을 직접 실행할 필요가 없습니다. `roblox-chat/README.md`의 순서대로 Workspace를 만들고 Init script를 붙여넣으면 됩니다.

## 실습자가 알아야 할 값

| 항목 | 값 |
| --- | --- |
| 공개 포트 | `7860` |
| 포트 이름 | `web-chat` |
| Roblox에 넣을 주소 | VESSL이 발급한 `https://...` 주소 |
| 준비 상태 확인 | 발급 주소 뒤에 `/ready` 추가 |

Roblox에는 `/ready`나 `/api/chat`을 제외한 기본 주소만 입력합니다.

## 로컬에서 실행하기

이 부분은 강사나 개발자만 사용합니다. 저장소 루트에서 Python 3.13 환경을 만들어 실행합니다.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r web-chat/requirements.txt
.venv/bin/python --version
.venv/bin/python web-chat/server.py
```

브라우저에서 `http://127.0.0.1:7860`을 엽니다. 모델 서버는 별도로 `http://127.0.0.1:8000/v1`에서 실행되어야 합니다.

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

초상 이미지 출처: [사용자 제공 이미지](https://i.namu.wiki/i/NoJSCwwjqsqwMongIdteq4u_NEqe8M2Gx5OXl_soI6axeLqpnfCwctoW5BWaKrq9LKECbYLhNxsEq504VmR7olICNq2bH8HU08w5u4FCcKcHdl1ykERQTjyFhfTLg56f4wNIcL54CxeEx_lCLtIErIbFIs5uiFkw9nGdtozKQ9c.webp)
