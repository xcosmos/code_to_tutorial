# Chapter 7: 인증 및 권한 (OAuth Provider, Auth Middleware)

## 1. 왜 인증·권한이 중요한가요? (Motivation)

지금까지 만든 MCP 서버는 여러 툴과 클라이언트의 요청을 처리할 수 있습니다. 하지만, **누가** 이 서버에 접근하는지, **허락받은 사용자**만 민감한 정보나 기능을 쓸 수 있도록 막는 것이 매우 중요합니다.

예를 들어, 어떤 사용자가 데이터베이스 삭제처럼 중요한 명령을 보내는데 **아무 검증 없이 허용**된다면, 서버가 쉽게 위험에 처할 수 있습니다.  
그래서 다음과 같은 기능이 필요합니다.

- 로그인/토큰 기반 **인증**(Authentication)  
- "어떤 권한까지 OK야?"를 판별하는 **권한검사**(Authorization)  
- 안전한 토큰 발급/폐기  
- 미들웨어 구조로 일관성 있게 요청마다 인증/권한 처리

이런 고민을 효율적이고 표준적인 방법으로 해결하는 것이 **OAuth2** 프로토콜이며, MCP 서버도 이를 지원하는 구조입니다!

---

## 2. 핵심 개념 이해하기 (Key Ideas)

1. **OAuth Provider**  
   - OAuth를 사용해 토큰을 발급, 갱신, 폐기, 클라이언트 등록 등을 처리합니다.
   - *"누구인가?"* "권한이 맞는가?" 등을 책임집니다.
   - 여러 메서드(`authorize`, `load_access_token` 등)로 추상적으로 설계되어, 다양한 방식으로 확장할 수 있습니다.

2. **Auth Middleware (인증 미들웨어)**
   - 요청마다 **토큰 헤더 확인→유효성 검사→권한 체크** 과정을 미들웨어로 처리합니다.
   - 인증/권한 정보를 컨텍스트(Context)에 담아 핸들러/툴에서 쉽게 활용할 수 있게 합니다.

3. **토큰(Token)**
   - Bearer 토큰(=짧은 액세스키 역할)으로, HTTP 요청에 포함해 검증합니다.
   - 유효기간/스코프(권한)가 존재합니다.

4. **클라이언트 등록 및 토큰 관리**
   - 서버에 새 앱(클라이언트) 등록, 토큰 주기/회수, 권한범위(스코프) 조정도 모두 이 계층에서 다룹니다.

---

## 3. 코드 살펴보기 (Code)

아래 코드는 MCP 인증 구조 중 주요 부분입니다.  
각 역할별로 차근차근 분해해 볼게요.

---

### [1] 인증 사용자 컨텍스트 관리 - `auth_context.py`

```python
# 인증된 사용자 정보를 요청 컨텍스트에 안전하게 저장
auth_context_var = contextvars.ContextVar[AuthenticatedUser | None](
    "auth_context", default=None
)

def get_access_token() -> AccessToken | None:
    auth_user = auth_context_var.get()
    return auth_user.access_token if auth_user else None

class AuthContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        user = scope.get("user")
        if isinstance(user, AuthenticatedUser):
            token = auth_context_var.set(user)
            try:
                await self.app(scope, receive, send)
            finally:
                auth_context_var.reset(token)
        else:
            await self.app(scope, receive, send)
```

#### ✦ 설명

- `ContextVar`는 요청마다 개별 사용자 정보를 안전하게 보관합니다.
- 미들웨어(`AuthContextMiddleware`)가 인증된 사용자를 `auth_context_var`에 할당해, 이후 핸들러들에서 `get_access_token()` 등으로 쉽게 가져올 수 있게 합니다.
- 만약 인증된 사용자가 없으면 기본값(`None`)으로 동작합니다.

---

### [2] Bearer 토큰 인증과 권한검사 - `bearer_auth.py`

```python
class AuthenticatedUser(SimpleUser):
    # 액세스 토큰·권한 정보 구축
    def __init__(self, auth_info: AccessToken):
        super().__init__(auth_info.client_id)
        self.access_token = auth_info
        self.scopes = auth_info.scopes

class BearerAuthBackend(AuthenticationBackend):
    # Authorization 헤더의 Bearer 토큰을 확인, 유효성 검사 등 진행
    def __init__(self, provider: OAuthAuthorizationServerProvider[Any, Any, Any]):
        self.provider = provider

    async def authenticate(self, conn: HTTPConnection):
        auth_header = conn.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        auth_info = await self.provider.load_access_token(token)

        if not auth_info:
            return None
        if auth_info.expires_at and auth_info.expires_at < int(time.time()):
            return None

        return AuthCredentials(auth_info.scopes), AuthenticatedUser(auth_info)

class RequireAuthMiddleware:
    # 지정한 스코프(권한)가 토큰에 포함되어있는지 검사
    def __init__(self, app: Any, required_scopes: list[str]):
        self.app = app
        self.required_scopes = required_scopes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        auth_user = scope.get("user")
        if not isinstance(auth_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Unauthorized")
        auth_credentials = scope.get("auth")

        for required_scope in self.required_scopes:
            if (
                auth_credentials is None
                or required_scope not in auth_credentials.scopes
            ):
                raise HTTPException(status_code=403, detail="Insufficient scope")
        await self.app(scope, receive, send)
```

#### ✦ 설명

- `BearerAuthBackend`는 요청 헤더의 Bearer 토큰을 꺼내와, OAuth Provider로 검증합니다.
- 검증이 성공하면, 사용자 타입과 권한 정보를 `scope`에 설정합니다.
- `RequireAuthMiddleware`는 꼭 필요한 스코프가 토큰에 있는지 다시 검증해, 부족할 경우 403 에러(권한부족)를 냅니다.

---

### [3] OAuth Provider 인터페이스 - `provider.py`

```python
class OAuthAuthorizationServerProvider(
    Protocol, Generic[AuthorizationCodeT, RefreshTokenT, AccessTokenT]
):
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        ...
    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        ...
    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        ...
    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCodeT | None:
        ...
    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCodeT
    ) -> OAuthToken:
        ...
    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshTokenT | None:
        ...
    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshTokenT,
        scopes: list[str],
    ) -> OAuthToken:
        ...
    async def load_access_token(self, token: str) -> AccessTokenT | None:
        ...
    async def revoke_token(
        self,
        token: AccessTokenT | RefreshTokenT,
    ) -> None:
        ...
```

#### ✦ 설명

- 다양한 OAuth 토큰/코드/권한 처리를 담당하는 "프로토콜 인터페이스"입니다.
- 직접 저장소, 외부 API 연동 등으로 쉽게 교체·확장할 수 있습니다.
- MCP 서버는 인증 토큰 발급, 갱신, 폐기, 클라이언트 등록까지 표준적으로 처리할 수 있게 됩니다.

---

### [4] OAuth 엔드포인트 라우팅 등록 - `routes.py`

```python
def create_auth_routes(
    provider: OAuthAuthorizationServerProvider[Any, Any, Any],
    issuer_url: AnyHttpUrl,
    service_documentation_url: AnyHttpUrl | None = None,
    client_registration_options: ClientRegistrationOptions | None = None,
    revocation_options: RevocationOptions | None = None,
) -> list[Route]:
    # ··· (설정 및 메타데이터)
    routes = [
        Route(
            "/.well-known/oauth-authorization-server",
            endpoint=...,
            methods=["GET", "OPTIONS"],
        ),
        Route(
            "/authorize",
            endpoint=...,
            methods=["GET", "POST"],
        ),
        Route(
            "/token",
            endpoint=...,
            methods=["POST", "OPTIONS"],
        ),
    ]
    # 클라이언트 등록·토큰 폐기 옵션에 따라 라우트 추가
    # ...
    return routes
```

#### ✦ 설명

- 실제로, MCP 서버가 지원하는 모든 인증 관련 HTTP 엔드포인트를 표준경로(`/.well-known/oauth-authorization-server`, `/authorize`, `/token` 등)로 정의합니다.
- 각 엔드포인트별로 필요 미들웨어와 인증 로직이 자동으로 연결되어, 다른 주요 기능과 분리(!)된 채 인증 처리를 담당하게 됩니다.

---

## 4. 마무리: 인증 기능을 서버에 손쉽게 연결하는 법 (Wrap-up)

MCP 서버는  
- 인증·인가(Authorization) 역할을 분리된 미들웨어와 OAuth Provider 인터페이스로 설계했고,
- 원하는 곳에 Bearer 토큰 인증, 스코프(권한) 검사, 클라이언트 등록 및 토큰 발급·폐기(Revocation)까지 손쉽게 활용할 수 있습니다.

이 구조 덕분에  
- 인증 로직, 권한처리, 클라이언트 앱 등록/관리 등은 핵심 HTTP 핸들러에서 독립적으로 다룰 수 있고,
- Context/미들웨어 패턴으로, 인증정보를 타입-세이프하게(안정적으로) 전달하며,
- OAuth2의 확장과 커스터마이즈도 자유롭게 가능합니다.

이제 여러분의 서버는  
**누구의 요청이든, "너 정말 이 기능 써도 돼?"를 묻고 지키는 튼튼한 경비실**을 갖추게 된 것입니다!

---

**마지막으로:**  
MCP 서버의 전체 구조에서는 매 요청마다  
- 라이프사이클 관리(리소스 초기화/정리),  
- context 기반 상태 및 진행로그 관리,  
- 최신 인증/권한 제어까지  
직관적이면서 견고하게 구현할 수 있습니다.

여기까지 MCP 서버 초보자 튜토리얼을 마칩니다.  
여러분만의 인증 정책과 툴을 자유롭게 붙여보세요! 🚀