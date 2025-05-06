# Chapter 6: 라이프스팬(Lifespan)과 컨텍스트 관리 (LifespanContext, Context)

---

## 동기 (Motivation)

프로그래밍에서 서버를 만들다 보면 이런 고민을 하게 됩니다:

- 서버를 켤 때 데이터베이스 연결이나 파일 오픈 등 한 번만 해도 되는 준비 작업은 어디서 할까?
- 매 요청(request)마다 누군가 오면, 진행 상황을 추적하고, 로그를 남기고, 그때그때 필요한 정보(예: 유저 정보, 인증 등)는 어떻게 잘 전달할까?
- 서버가 종료(죽을 때) 할 땐, 어떤 자원을 안전하게 정리(정리하고 닫기) 할 수 있지?

이런 문제를 깔끔하게 해결하려면 '생명주기(라이프사이클) 관리'와 '컨텍스트(context)'라는 개념이 필요합니다.  
MCP 서버는 이 부분의 추상화가 매우 잘 되어 있어서, 실무 코드에서 안전하면서도 편리하게 다룰 수 있습니다.

---

## 핵심 개념 (Key Ideas)

### 1. 라이프스팬(Lifespan)

- 서버 시작과 종료 시에만 한 번 수행하는 준비/정리 작업을 처리하는 구조입니다.
- 예시: 데이터베이스 연결, configuration 로딩, 파일 오픈/정리 등.
- 별도의 '라이프스팬 컨텍스트' 객체(LifespanContext)에 이 정보를 저장해두고, 요청 시 사용할 수 있게 전달합니다.

### 2. 컨텍스트(Context)

- 요청마다 한 번씩 "현재 상황 정보를 묶은 꾸러미"를 만들어, 핸들러 함수에 넘겨줍니다.
- 이 컨텍스트에는 다음과 같은 정보/기능이 있습니다:
    - 요청 ID, 클라이언트 ID 등 메타정보
    - (선택적으로) 로그인 유저 정보, 인증 토큰 등 인증 관련 정보
    - 로그(디버그/정보/경고/오류) 메시지 전송
    - 진행 상황 보고 (프로그레스)
    - 자원(리소스) 읽기
    - 세션 등 고급 기능

이 덕분에 복잡한 글로벌 변수 없이, 타입이 보장된 안전한 의존성 주입처럼 코드를 작성할 수 있습니다.

---

## 코드

아래에서 핵심 개념별로 부분 코드를 나누어 살펴본 후, 각각 어떤 역할을 하는지 쉽게 설명해드릴게요.

---

### 1. 라이프스팬(Lifespan) 컨텍스트 관리

#### 라이프스팬 설정

서버 옵션에서 `lifespan`을 별도로 지정할 수 있습니다.

```python
class Settings(BaseSettings, Generic[LifespanResultT]):
    # ... (생략)
    lifespan: (
        Callable[[FastMCP], AbstractAsyncContextManager[LifespanResultT]] | None
    ) = Field(None, description="Lifespan context manager")
    # ... (생략)
```

#### 라이프사이클 관리 래퍼

서버가 켜질 때/꺼질 때 준비/정리 작업을 해주는 함수를 작성할 수 있습니다.

```python
def lifespan_wrapper(app, lifespan_fn):
    @asynccontextmanager
    async def wrap(s):
        async with lifespan_fn(app) as context:
            yield context
    return wrap
```

- 사용자가 준비/정리 코드가 담긴 lifespan 함수를 넘겨주면,
- 서버가 실행될 때 context를 얻어 각 요청 처리 중에도 안전하게 쓸 수 있게 만듭니다.

예시:
```python
async def startup_and_cleanup(app):
    db = await some_async_db_connect()
    try:
        yield {"db": db}
    finally:
        await db.disconnect()
        
settings = Settings(lifespan=startup_and_cleanup)
server = FastMCP(**settings.dict())
```

이렇게 하면 서버 실행 시 한 번 연결, 꺼질 때 한 번 정리!

---

### 2. 요청 컨텍스트(Context) 구조

#### 컨텍스트 구조체

요청별로 아주 중요한 정보들을 하나로 묶는 구조가 있습니다.

```python
@dataclass
class RequestContext(Generic[SessionT, LifespanContextT]):
    request_id: RequestId
    meta: RequestParams.Meta | None
    session: SessionT
    lifespan_context: LifespanContextT
```

요약하면:
- **request_id:** 각 요청마다 구분하는 ID
- **meta:** 부가정보(예: 클라이언트ID, 인증 등)
- **session:** 요청중 세션 정보(예: 커넥션/사용자 등)
- **lifespan_context:** 서버 전체 공용(한 번만 준비된 정보; 예: DB 커넥션)

#### 툴/핸들러에 주입되는 'Context' 객체

MCP에서는 함수에 `Context` 타입 파라미터를 추가하면, 위의 정보가 자동으로 제공됩니다.

```python
class Context(BaseModel, Generic[ServerSessionT, LifespanContextT]):
    _request_context: RequestContext[ServerSessionT, LifespanContextT] | None
    _fastmcp: FastMCP | None

    # ... (생략)

    @property
    def request_id(self):
        return str(self.request_context.request_id)

    @property
    def client_id(self):
        # 인증 정보 있으면 클라이언트ID 제공
        return getattr(self.request_context.meta, "client_id", None)
    
    async def read_resource(self, uri):
        assert self._fastmcp is not None
        return await self._fastmcp.read_resource(uri)

    async def info(self, message):
        await self.log("info", message)

    async def report_progress(self, progress, total=None):
        # 클라이언트로 진행상황 전송
        progress_token = (
            self.request_context.meta.progressToken
            if self.request_context.meta
            else None
        )
        if progress_token is not None:
            await self.request_context.session.send_progress_notification(
                progress_token=progress_token, progress=progress, total=total
            )
```

#### 실제 사용 예시

아래처럼 함수 선언에 `Context` 타입 파라미터를 추가하고, 유사한 "작업환경" 정보에 접근할 수 있습니다.

```python
@server.tool()
def my_tool(x: int, ctx: Context):
    # 로그 남기기
    await ctx.info(f"Input값은 {x}입니다.")
    # 진행상황 알리기
    await ctx.report_progress(1, 10)
    # 리소스 접근
    data = await ctx.read_resource("resource://data")
    # 요청자(클라이언트) ID 체크
    print(ctx.client_id)
    return "처리 결과"
```

이렇게 하면, 단일 함수 안에서도 "현재 요청의 문맥"에 안전하게 접근할 수 있습니다.

---

## 해설 (Explanation)

### 왜 Lifespan이 필요한가요?

서버는 끄고 켤 때 자주 거치는 작업들이 있습니다. (예: 데이터베이스나 캐시 연결/해제)

- 만약 이런 코드를 매 요청마다 한다면? → 불필요하게 느리고 비효율적!
- 전체 서버 시작/종료(한 번)만 하고 싶다면? → Lifespan 컨텍스트에 정의하면 자동 처리.

### 요청별 Context가 왜 중요한가요?

서버가 동시에 여러 클라이언트의 요청을 받아 처리할 땐,
- 이 요청이 누가 보낸 건지, 어떤 인증정보를 지녔는지,
- 내가 진행 중인 작업을 서로 다른 리퀘스트들이 섞이지 않게 안전하게 관리해야 합니다.

파이썬에서는 전역변수나 글로벌 상태 대신, 이런 정보를 '컨텍스트'라는 구조로 각 요청에 "꾹" 묶어서 넘깁니다.
이렇게 하면,
- 코드가 명확해지고,
- 버그가 줄어들며,
- 타입체크/IDE 지원이 좋아집니다.

### 어떤 함수에서 Context를 받을 수 있나요?

- MCP의 도구(툴), 자원(리소스), 프롬프트 등에서 `Context` 타입 파라미터를 선언하면 자동 주입됩니다.
- (선언하지 않으면 안 들어갑니다. 하지만 필요한 함수만 사용!)

### Context로 할 수 있는 일?

- 요청 ID, 클라이언트ID, 인증 등 메타정보 읽기
- 로그(Info/경고/오류/디버그) 남기기
- 진행상황(progess) 알리기
- 외부 자원(resource) 읽기/쓰기
- 고급: 세션, lifespan context 등도 접근

---

## 요약 (Wrap-up)

MCP 서버에서 'Lifespan'과 'Context'는 "안전하고, 편리한 서버 코드"의 핵심 비밀입니다.

- Lifespan 컨텍스트는 서버 전체 실행 중 한 번 준비되는 정보(예: DB연결 등)를 책임집니다.
- Context는 각 요청별 다양한 정보(요청ID/로그/프로그레스/자원접근 등)를 안전하게 함수에 주입하는 구조입니다.

이 두 구조를 잘 활용하면, 복잡한 동시성/의존성 문제도 간단하게 해결할 수 있습니다.

다음 장에서는 인증 및 권한 관리(OAuth Provider, Auth Middleware)로 이어집니다! 🚀