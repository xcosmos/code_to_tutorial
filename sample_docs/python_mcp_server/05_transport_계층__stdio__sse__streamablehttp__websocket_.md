# Chapter 5: Transport 계층 (Stdio, SSE, StreamableHTTP, Websocket)

---

## 동기 (Motivation)

우리가 앞장까지 배운 MCP 서버/클라이언트 아키텍처는 ‘어떻게’ 데이터를 주고받을지 규정하지 않았습니다. 즉, MCP를 “서버”와 “클라이언트”가 서로 메시지를 주고받는 방식만 정해뒀을 뿐,  
**실제로 데이터를 어떤 통로(네트워크·프로세스)로 전달할지는 자유롭게 고를 수 있습니다.**

인터넷에서 통신하려면 HTTP, 웹소켓, 프로세스 간 통신 등 여러 가지 방식이 존재합니다. 하나만 쓴다면 구현이 쉽겠지만,  
- 로컬 개발, 배포, 데스크탑앱/웹앱/명령어 등 다양한 환경마다 요구사항이 다릅니다.
- 스트림, 실시간성, 연결복구, 브라우저·방화벽 호환성 등 목적마다 장단점이 있습니다.

그래서 MCP는 여러 **트랜스포트 계층** 모듈을 제공해 **‘동일한 메시지 구조로, 다양한 통신 방식’을 쓸 수 있도록** 만들어졌습니다!

---

## 핵심 개념 (Key Ideas)

### 1. 트랜스포트란?
> 데이터를 실제로 '주고받는' 통로(네트워크 커넥션, 파이프 등)를 추상화한 모듈

### 2. 왜 여러 가지 트랜스포트가 필요한가?
- 환경과 목적, 개발 언어 등에 따라 최적의 방식이 다르기 때문
    - 예) 로컬 실행은 stdio/파이프, 브라우저 기반은 SSE/웹소켓, 긴 스트리밍은 StreamableHTTP

### 3. MCP에서 제공하는 트랜스포트 종류
- **Stdio**: 프로세스 간 표준 입력/출력으로 통신 (주로 로컬에서 커맨드 실행/ภาษา파이프 전용)
- **SSE (Server-Sent Events)**: 서버가 클라이언트로 "one-way" 스트리밍 (브라우저 지원, 간단함)
- **StreamableHTTP**: HTTP(S)로 요청/응답을 스트림까지 지원·최신 REST/JSON API와 연동에 적합
- **Websocket**: 실시간 양방향 통신, 브라우저/데스크탑 앱/모바일 앱 등에서 활용

각 방식마다,
- 내부에서 **메시지 스트림**(읽기/쓰기)을 만들고,
- 받은/보낼 메시지는 **항상 동일한 MCP 프로토콜 데이터 구조(types.py에서 정의된 것)**에 맞춤
- 사용자는 “이 트랜스포트로 내가 데이터를 어떻게 주고받는가?”만 신경 쓰면 됨

---

## 코드와 단계별 설명 (Code & Step-by-step Explanation)

아래 예시들은 트랜스포트 계층이 **명확히 구분된 파일**로 모듈화 되어있을 뿐,  
**패턴(인터페이스)**은 거의 동일합니다.

---

### 1. Stdio 트랜스포트

- 로컬 환경에서 별도 프로그램을 **프로세스(popen)로 띄우고**,  
  프로세스의 표준입력(stdin)/표준출력(stdout)으로 데이터를 주고받는 구조입니다.

#### 주요 흐름
1. MCP 서버를 **실행할 명령어/환경**을 정의
2. 프로세스 실행 (`anyio.open_process`)
3. **입력 스트림**(서버→클라이언트) / **출력 스트림**(클라이언트→서버) 파이프 연결
4. 읽기/쓰기는 메모리 스트림(버퍼)을 사용하여,  
   하나씩 MCP 메시지를 파싱 후 처리

#### 즉,  
- 내가 입력하면 MCP 메시지가 새 프로세스(서버)에 전달되고,
- 서버가 답하면 메모리스트림에 씨어짐

---

### 2. SSE (Server-Sent Events) 트랜스포트

- 주로 **브라우저 등에서 서버의 실시간 푸시 알림**(One-way streaming)을 하고 싶을 때 사용
- `GET`으로 SSE 커넥션을 열고, 서버에서 이벤트가 도착하면 실시간으로 들어옴  
  (클라에서 요청을 보내려면 별도로 `POST` 사용)

#### 주요 흐름
1. 클라이언트가 **SSE 엔드포인트**에 연결 → 서버가 유니크 세션 URL 리턴
2. 한쪽(`write_stream`)은 `POST`로 메시지 전송,  
   다른 한쪽(`read_stream`)은 SSE 스트림으로 서버에서 날아오는 이벤트 수신
3. 읽은 이벤트는 MCP 메시지 구조에 맞춰 파싱&버퍼  
   (이 때 유효성검사 등은 types.py(모델) 기준)

---

### 3. StreamableHTTP 트랜스포트

- **최신 HTTP API 스타일**, `POST`는 바로 메시지 보내기,  
  서버 응답은 “JSON 한 번” 혹은 “스트림(SSE)처럼 점진적으로” 받을 수 있음
- 대량의 데이터 처리나,  
  서버에서 긴 작업(딥러닝, 배치처리 등) 할 때 이용도가 높음

#### 주요 특징
- **초기화/세션ID를 활용한 계속성 지원**  
  (중간에 연결 끊겨도 재접속·재시작 가능)
- `GET`은 서버에서 클라로만 이벤트 푸시 (2차 스트림)
- **핵심**:  
   기존 HTTP+SSE 특성을 결합, 하나의 API로 유연하게 지원

---

### 4. Websocket 트랜스포트

- 실시간 채팅, 온라인 게임 등에서 흔히 쓰는 “양방향 통신” 기술입니다.
- 연결이 살아있는 동안 데이터를 자유롭게 주고받고,  
  메시지가 오고가면 바로바로 반응 가능

#### 주요 흐름
1. 클라이언트에서 webSocket 연결 열기 (`ws_connect`)
2. **메시지 읽기/쓰기**를 별도의 비동기 함수로 분리  
   (읽는 중에 쓸 수도, 동시에 여러 연산도 가능)
3. 데이터는 무조건 MCP 메시지 구조(JSON-RPC 스타일)로 파싱/검증

---

## 실제 코드 예시/분해: (코드 → 해설)

---
### [예시 1] 클라이언트용 Websocket 트랜스포트 골격

```python
@asynccontextmanager
async def websocket_client(
    url: str,
) -> AsyncGenerator[
    tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ],
    None,
]:
    # (생략) ...

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    async with ws_connect(url, subprotocols=[Subprotocol("mcp")]) as ws:
        async def ws_reader():
            async with read_stream_writer:
                async for raw_text in ws:
                    # JSON 메시지 파싱, 실패시 Exception으로 전달
                    try:
                        message = types.JSONRPCMessage.model_validate_json(raw_text)
                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
                    except ValidationError as exc:
                        await read_stream_writer.send(exc)

        async def ws_writer():
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    msg_dict = session_message.message.model_dump(
                        by_alias=True, mode="json", exclude_none=True
                    )
                    await ws.send(json.dumps(msg_dict))

        async with anyio.create_task_group() as tg:
            tg.start_soon(ws_reader)
            tg.start_soon(ws_writer)
            yield (read_stream, write_stream)
            tg.cancel_scope.cancel()
```

#### 해설
- **스트림 생성**: (읽기/쓰기) 메모리 기반 스트림 쌍을 만든다.
- **연결 진행**: ws_connect로 웹소켓을 연결(`mcp` 프로토콜 사용)
- **ws_reader**:  
   서버로부터 전달받는 메시지들을 계속 읽으면서  
   → JSON 파싱 → SessionMessage 객체로 변환 → read_stream_writer에 삽입  
   (파싱 실패시에도 Exception 전달)
- **ws_writer**:  
   write_stream_reader로부터 쌓인 메시지들을 읽어서  
   → JSON dump → ws.send로 서버로 전달함
- **anyio.create_task_group()**:  
   위의 reader/writer를 비동기로 동시에 돌림

**즉,**  
- 내가 write_stream에 메시지 넣으면 서버로 데이터 전송,  
  서버가 보내는 메시지는 read_stream으로 읽음  
- 내부 데이터 구조(메시지)는 MCP 표준만 따름→  
  사용자는 트랜스포트의 방식만 고르면 됨

---

### [예시 2] 서버용 StreamableHTTP 트랜스포트 (핵심부분)

- 클라이언트가 POST로 JSON 메시지 → MCP 파싱 → 응답은 SSE 또는 JSON 형태로 스트림 전송
- 각 요청마다 별도의 메시지 스트림을 만듦  
- RequestId 등 메타데이터 기반으로 메시지를 라우팅

#### 주요부분 해설

- 먼저 요청의 Content-Type, Accept 헤더 확인  
   (json, sse를 동시에 지원해야 함)
- POST일 때, `initialize` 요청이면 세션 체킹/초기화
- 일반 메시지는 세션 체크 후 메모리스트림에 MCP 메시지로 보냄
- **응답방식**  
    - JSON-RPC "요청"이면 별도 리더를 만드는 방식 (서버가 스트림으로 계속 이벤트를 쏠 수 있음)
    - 단일 응답(json) 모드도 옵션으로 지원
- **GET**은 "서버가 클라이언트로 직접 메시지"를 보낼 때 (알림, 통지 등)
- **DELETE**는 세션 정리, 스트림 모두 종료

**추상화 포인트**:  
- 내부의 모든 로직은 ‘messages를 적절한 스트림에 넣고,  
  스트림을 Response/SSE(ws, http 등)로 연결’  
- 어떤 트랜스포트이든 “언제나 동일한 MCP 메시지 구조만 사용”

---

## 정리 및 실전 팁 (Wrap-up)

### 1. 트랜스포트 계층의 장점
- **확장성**: 트랜스포트 방식 추가/변경이 용이 (동일한 MCP 메시지 구조만 따르면 됨)
- **유지보수성**: 서버-클라가 어떤 전송 방법을 쓰든 내부 로직 코드 불변
- **유연성**:  
   Web 환경, 데스크탑, 명령어, 네이티브앱 등  
   상황에 맞게 트랜스포트만 바꿔 쉽게 프로토콜/서버를 재활용 가능

### 2. 실제 적용 예시
- 로컬에서 빠르게 실험: **Stdio** 사용 (프로토타입, Jupyter연동 등)
- 웹앱/브라우저 연동: **SSE·Websocket** 선택 (실시간성·호환성 고려)
- 서버-서버 API, 장시간 작업: **StreamableHTTP** 추천 (스트림/복원성 지원)

### 3. 실용적인 패턴
- **메시지 구조와 트랜스포트는 완전 분리되어 있음**  
  (비즈니스 로직은 “받은 메시지”만 파싱/처리/응답)
- 각 트랜스포트에서 “스트림(읽기/쓰기)/세션ID/에러 처리” 등이 표준화됨  
  → 빠른 테스트/운영 환경 전환이 가능

---

### 아날로지로 이해:  
- “메일(메시지)”은 항상 같은 모양!  
   *단지 등기(HTTP), 택배(SSE), 비행기(Websocket) 등  
   적합한 운송수단만 골라서 보내는 것!*  

---

## 다음 장에서

이제 메시지가 **안전하게 잘 전송**되는 통로를 만들었으니,  
서버가 시작/종료 및 각 요청 마다 리소스/컨텍스트를 안정적으로 관리하는  
**라이프스팬 & 컨텍스트 패턴**을 배웁니다! (→ Chapter 6)  
**서버 전체 생명주기/의존성 관리, 실행 맥락 이슈**를 풀어나가 보겠습니다.

---

> **이 장의 핵심**  
> 트랜스포트 모듈은 MCP 시스템을 다양한 환경·목적으로  
> “동일한 메시지 구조로, 다양한 전송 채널을 선택해서”  
> 개발/배포/운영할 수 있게 해주는 “인터페이스의 핵심”입니다!