# Chapter 3: MCP 메시지/통신 시스템 (SessionMessage, RequestResponder, BaseSession)

---

## 1. 왜 이런 통신 계층이 필요할까요?

우리가 만드는 MCP 서버와 클라이언트는 서로 떨어진 환경에서 동작할 수 있습니다. 
예를 들어, 한 쪽은 로컬에서, 다른 한 쪽은 네트워크 넘어에 있거나 심지어 같은 메모리 안에서 통신할 수도 있죠.  
이 다양한 환경에서도 **서로 말을 쉽게 주고받으려면** 공통되는 "메시지 규칙"이 필요합니다. 

예를 들어, 카카오톡, 슬랙 같은 메신저를 생각해보면,  
누가 누구에게 어떤 내용을 보냈는지, 답장은 어떻게 받는지, "읽었음" 같은 알림은 어떻게 전달하는지  
알아서 잘 동작하도록 규칙과 형태가 정해져 있습니다.

MCP의 메시지/통신 계층이 바로 이런 역할을 합니다.  
실드처럼 네트워크/메모리/비동기 처리의 어려움을 감추고,  
개발자는 "메시지를 보낸다/받는다"라는 관점으로만 기능을 구현할 수 있습니다.

---

## 2. 핵심 개념 살펴보기

### 2-1. **SessionMessage**

- MCP에서 한 번 주고받는 "메시지"의 기본 단위입니다.
- 메시지 자체와, 추가적인 정보(예: 어느 메시지에 대한 응답인지, 재시작 정보 등)를 함께 담습니다.
- 예: 카톡에서 보낸 메시지에 "읽음표시"나 "답장대상" 정보가 붙는 것과 비슷!

### 2-2. **RequestResponder**

- 클라이언트/서버가 "요청"을 보냈을 때,  
  이에 대한 "응답"을 제대로 안전하게 보내는 컨트롤러 같은 역할입니다.
- 사용 예시:
    - 요청 처리 도중 오류나 취소가 나더라도,  
      한 번만 응답, 취소, 완료 상태를 보장합니다.
    - 컨텍스트 매니저(파이썬 with문)를 사용해 꼭 종료 처리가 이뤄집니다.
- 예: 친구가 카톡을 보냈을 때,  
  반드시 답장을 하거나 '취소됨' 알람을 보내는 휴대폰 앱의 내부 로직과 비슷!

### 2-3. **BaseSession**

- MCP 세션의 "메인 엔진"입니다.
- 메시지 스트림(네트워크/메모리 등 어디서든!) 위에  
  "요청 → 응답 / 알림"이라는 규칙을 올려서 작동합니다.
- 비동기 컨텍스트 매니저로 시작·종료, 메시지 자동 수신, in-flight 요청 관리 같은  
  복잡한 과정을 알아서 처리해줍니다.
- 덕분에 개발자는 "서버/클라이언트가 이 함수만 오버라이드하면 된다!"  
  수준의 간단한 인터페이스만 신경 쓰면 됩니다.

---

## 3. 코드 살펴보기

### 3-1. SessionMessage – 메시지 감싸기와 부가 정보

```python
@dataclass
class SessionMessage:
    """전송 전용 메타데이터와 함께 메시지를 감싸는 래퍼 클래스"""

    message: JSONRPCMessage        # 실제 메시지(요청/응답/알림 등)
    metadata: MessageMetadata = None  # 재시도 토큰, 관련 요청 ID 등 부가 정보
```

**설명:**  
- 어떤 메시지(예: 'resoures/list 요청', 'sampling 요청', '로그 알림')라도  
  다 `SessionMessage`로 감싸서 보냅니다.
- `metadata`는 예를 들어 "이 응답이 어느 요청에 대한 결과다", "중간에 중단됐을 때 이어서 받을 수 있는 토큰" 같은 정보 저장용입니다.

---

### 3-2. RequestResponder – 요청에 대한 서버의 응답 컨트롤러

```python
class RequestResponder(Generic[ReceiveRequestT, SendResultT]):
    ...
    def __enter__(self):
        self._entered = True
        self._cancel_scope = anyio.CancelScope()
        self._cancel_scope.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._completed:
                self._on_complete(self)
        finally:
            self._entered = False
            if not self._cancel_scope:
                raise RuntimeError("No active cancel scope")
            self._cancel_scope.__exit__(exc_type, exc_val, exc_tb)

    async def respond(self, response: SendResultT | ErrorData) -> None:
        if not self._entered:
            raise RuntimeError("RequestResponder must be used as a context manager")
        assert not self._completed, "Request already responded to"

        if not self.cancelled:
            self._completed = True
            await self._session._send_response(
                request_id=self.request_id, response=response
            )

    async def cancel(self) -> None:
        if not self._entered:
            raise RuntimeError("RequestResponder must be used as a context manager")
        if not self._cancel_scope:
            raise RuntimeError("No active cancel scope")

        self._cancel_scope.cancel()
        self._completed = True
        await self._session._send_response(
            request_id=self.request_id,
            response=ErrorData(code=0, message="Request cancelled", data=None),
        )
```

**설명:**  
- 클래스를 `with` 구문(컨텍스트 매니저)으로 반드시 사용해야 합니다.
- 요청 처리 중 에러가 나도, 취소가 돼도, 응답을 반드시 한 번만 보내도록 강제합니다.
- 취소가 오면 자동으로 취소 응답을 보냅니다.
- `respond()`는 요청에 대한 정상 응답/에러 응답을 보냅니다.  
  이미 응답됐다면 두 번 보낼 수 없습니다.
- `cancel()`은 요청을 취소하고 "취소됨" 응답을 보냅니다.

---

### 3-3. BaseSession – MCP 통신의 핵심 엔진

#### 생성 및 초기화

```python
class BaseSession(...):
    def __init__(
        self,
        read_stream,             # 들어오는 메시지 스트림 (메모리, 네트워크 등)
        write_stream,            # 나가는 메시지 스트림
        receive_request_type,    # 어떤 형태의 요청을 받을지
        receive_notification_type, # 어떤 형태의 알림을 받을지
        read_timeout_seconds=None, # (선택) 응답 대기 시간 제한
    ):
        self._read_stream = read_stream
        self._write_stream = write_stream
        ...
        self._response_streams = {}   # 요청 ID별 응답 스트림 저장
        self._request_id = 0          # 송신용 시퀀스 번호
        self._in_flight = {}          # 진행 중인 요청 목록
        self._exit_stack = AsyncExitStack()
```

**설명:**  
- 입력/출력 스트림이 실제 통신(메모리, 네트워크 등)을 추상화합니다.
- 요청을 보낼 때마다 내부에서 시퀀스 번호(ID)를 관리, 응답이 돌아오면 요청-응답을 정확히 연결합니다.
- 진행 중 요청(`_in_flight`)만 따로 관리해 취소, 에러 등도 쉽게 처리합니다.

---

#### 요청 보내기

```python
async def send_request(self, request, result_type, ...):
    request_id = self._request_id
    self._request_id += 1

    # 응답 받을 임시 스트림 생성
    response_stream, response_stream_reader = anyio.create_memory_object_stream(1)
    self._response_streams[request_id] = response_stream

    try:
        # 실제 JSON-RPC 메시지 만들기
        jsonrpc_request = JSONRPCRequest(
            jsonrpc="2.0",
            id=request_id,
            **request.model_dump(...)
        )
        # SessionMessage로 감싸서 발송
        await self._write_stream.send(
            SessionMessage(message=JSONRPCMessage(jsonrpc_request), metadata=metadata)
        )
        ...

        # 응답이 올 때까지(혹은 타임아웃까지) 대기
        with anyio.fail_after(timeout):
            response_or_error = await response_stream_reader.receive()

        # 응답이 에러면 에러 발생, 아니면 결과 반환
        if isinstance(response_or_error, JSONRPCError):
            raise McpError(response_or_error.error)
        else:
            return result_type.model_validate(response_or_error.result)
    finally:
        # 정리
        self._response_streams.pop(request_id, None)
        await response_stream.aclose()
        await response_stream_reader.aclose()
```

**설명:**
- 요청마다 고유 ID를 부여, 결과를 받을 스트림도 별도로 만듭니다.
- 실제로는 JSON 형태의 메시지를 표준대로 감싸서 내보내고,  
  들어오는 응답에서 ID로 내 요청과 찾아서 연결해줍니다.
- 응답이 지연되면 타임아웃(기다리는 최대 시간)도 적용할 수 있습니다.
- 에러면 예외로, 아니면 파싱해서 반환합니다.

---

#### 메시지 수신 루프

```python
async def _receive_loop(self):
    async with (self._read_stream, self._write_stream):
        async for message in self._read_stream:
            if isinstance(message, Exception):
                await self._handle_incoming(message)
            elif isinstance(message.message.root, JSONRPCRequest):
                validated_request = self._receive_request_type.model_validate(...)
                responder = RequestResponder(...)
                self._in_flight[responder.request_id] = responder
                await self._received_request(responder)
                if not responder._completed:
                    await self._handle_incoming(responder)
            elif isinstance(message.message.root, JSONRPCNotification):
                ...
            else:  # 응답/에러 메시지 처리
                stream = self._response_streams.pop(message.message.root.id, None)
                if stream:
                    await stream.send(message.message.root)
                else:
                    await self._handle_incoming(
                        RuntimeError("Received response with an unknown request ID")
                    )
```

**설명:**  
- 끊임없이 입력 스트림을 따라 들어오는 메시지를 받습니다.
- 요청(JSONRPCRequest)이면 파싱 → `RequestResponder`로 감싸 → 직접 처리합니다.
- 알림(JSONRPCNotification)이면 필요한 콜백/처리 함수를 실행합니다.
- 응답/에러(JSONRPCResponse/JSONRPCError)는 
  저장했던 응답 스트림에 연결해줄 수 있도록 재전달합니다.
- 만약 모르는 ID로 응답이 오면(실수!) 예외로 기록합니다.

---

#### 요청/알림 처리 확장점

- `_received_request(responder: RequestResponder)`  
  → 각 클라이언트/서버 구현에서 실제 내용 처리를 여기에 오버라이드합니다.
- `_received_notification(notification)`  
  → 알림이 들어왔을 때도 마찬가지로 처리할 수 있습니다.

-> 덕분에 "표준화된 메시지 처리"만 베이스에서 담당하고,  
"비즈니스 로직"은 각 앱에서 간단하게 오버라이드 해서 구현할 수 있습니다.

---

## 4. 정리

- **SessionMessage:** 메시지에 부가정보를 붙여 안전하게 송수신
- **RequestResponder:** 요청-응답의 생명주기를 철저하게 관리하고 보장
- **BaseSession:** 스트림 위에서 MCP 프로토콜 메시지의 송신, 수신, 요청/응답 관리 등 "인프라 엔진" 역할

이 구조는  
- 네트워크에 무관하게 안전하게 통신이 가능하고(비동기 스트림, 메모리/네트워크 구애 없음)
- 요청-응답, 알림, 취소, 오류 등 프로토콜의 어려운 부분을 모두 공통 처리해
- 사용자(서버/클라이언트 앱)는 필요한 기능만 간단히 덮어써서 개발할 수 있습니다.

다음 장에서는 실제로 MCP에서 사용하는 "데이터 구조와 규약(types.py)"를 자세히 살펴봅니다.

---

**핵심 기억!**  
- "메시지-요청-응답-알림"의 규칙,  
- 안전하고 일관적인 통신 방식의 핵심을 이 계층이 잡고 있다!  
- 코드는 조금 복잡해보여도, 실제 사용 시에는 "함수만 덮어써서"  
  내가 구현하는 MCP 서버/클라이언트가 안정적으로 동작한다는 큰 장점이 있습니다.