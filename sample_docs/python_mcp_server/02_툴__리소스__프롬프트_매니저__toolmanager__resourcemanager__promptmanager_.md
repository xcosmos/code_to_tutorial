# Chapter 2: 툴, 리소스, 프롬프트 매니저 (ToolManager, ResourceManager, PromptManager)

---

## 왜 이 개념이 필요한가요? (Motivation)

MCP 서버는 단순히 "메시지만 주고받는 통신소"가 아닙니다.  
실제 어플리케이션에서 중요한 것은 **서버가 가진 "기능(도구)", 데이터(리소스), 그리고 대화 프롬프트(질문/안내 문장 템플릿)** 입니다.

- 챗봇에선 → 프롬프트(질문/답변 패턴)
- 파일서버에선 → 리소스(파일/이미지)
- 자동화/AI시스템에선 → 여러 기능(도구, Tool)

이렇게 **서버가 외부로 제공할 수 있는 모든 것**을 한 곳에 등록/관리해주는 역할이 바로  
**툴매니저(ToolManager), 리소스매니저(ResourceManager), 프롬프트매니저(PromptManager)** 입니다.

---

## 핵심 아이디어 (Key Ideas)

- **ToolManager**  
  다양한 파이썬 함수(도구, 기능)를 서버에 "이름" 붙여서 등록하고, 필요할 때 찾아 실행합니다.  
  (예: 계산기 기능 만들고 `add`라는 이름으로 등록)

- **ResourceManager**  
  서버에서 제공하는 각종 리소스(이미지, 텍스트, 파일, 폴더 등)를 등록·관리합니다.  
  "리소스"란? 웹의 `/img/hello.png` 처럼 경로(uri)로 접근하는 실제 데이터.

- **PromptManager**  
  LLM이나 챗봇, 자동화 워크플로우용 **프롬프트(문자열 템플릿, 질문 양식 등)** 을 등록하고 불러씁니다.

이 매니저들에 **등록만 하면** 모든 클라이언트와 서버가 자연스럽게 API로 접근할 수 있습니다.

---

## 코드로 이해하기 (Code with Step-by-Step Explanation)

### 1. ToolManager (도구 매니저)

#### 등록 및 관리

파이썬의 함수를 "도구"로 등록해 서버에서 호출할 수 있게 합니다.

```python
tool = Tool.from_function(
    fn,
    name=name,
    description=description,
    annotations=annotations,
)
```

- `fn`: 실제 실행할 파이썬 함수
- `name`: 도구의 이름 (API에서 사용)
- `description`: 설명
- `annotations`: 추가 정보(옵션)

등록할 때, 중복된 이름이 있으면 경고만 하고 기존 걸 사용합니다.

#### 실사용 - 도구 호출

`ToolManager`는 이름으로 찾아서, 올바른 인자를 전달해 실행합니다.

```python
async def call_tool(self, name: str, arguments: dict, ...):
    tool = self.get_tool(name)
    if not tool:
        raise ToolError(f"Unknown tool: {name}")
    return await tool.run(arguments, context=context)
```

**정리하면:**  
- 파이썬 함수를 Tool로 감싼 뒤, 이름→실행 매핑이 자동으로 됩니다.
- 인자 검증도 Pydantic으로 수행합니다.

---

### 2. ResourceManager (리소스 매니저)

#### 리소스 등록

리소스(텍스트, 바이너리, 파일, HTTP 등)는 `Resource`라는 공통 클래스 기반으로 각각 구현되어 있습니다.

등록 예시:

```python
resource = TextResource(name="hello", uri="resource:hello", text="world!")
resource_manager.add_resource(resource)
```

- `name`: 이름(설명용)
- `uri`: 리소스 식별자(주소)
- 등록 시 같은 uri면 경고만 하고 무시

#### 리소스 템플릿

동적으로 리소스가 생성되는 경우 "템플릿"을 등록할 수 있습니다.  
예를 들어 `/file/{filename}` 패턴에 맞추면 접근할 때마다 실제 파일을 읽어서 제공합니다.

등록 예시:

```python
resource_manager.add_template(
    my_func,     # uri 패턴에 매칭되는 함수
    "/file/{filename}",
    name="file_resource"
)
```

- 실제 "접근"이 일어날 때만 해당 리소스를 만듭니다 (게으른 생성).

#### 리소스 조회

```python
resource = await resource_manager.get_resource("resource:hello")
content = await resource.read()
```

---

### 3. PromptManager (프롬프트 매니저)

#### 프롬프트 등록

챗봇/AI 등 대화형 시스템에서 "프롬프트"란, 미리 정의된 입력/출력 템플릿입니다.  
함수로 작성 후 등록합니다.

```python
def simple_prompt(name: str):
    return f"안녕하세요, {name}님!"

manager.add_prompt(Prompt.from_function(simple_prompt, name="hello_prompt"))
```

- 프롬프트는 파라미터(인자) 스키마까지 자동 추출(Pydantic 활용).

#### 프롬프트 렌더링

이름과 인자를 넘기면, Prompt가 실행되고 그 결과(메시지 리스트)를 반환합니다.

```python
messages = await manager.render_prompt("hello_prompt", {"name": "철수"})
```

---

## 한 단계 더 자세히 (설명)

### ToolManager가 파이썬 함수를 다루는 법

1. `from_function` 메서드로 파이썬 함수→Tool 인스턴스로 변환 (메타데이터 자동 추출)
2. 이름 중복 검사 후 딕셔너리(이름→Tool)로 저장
3. 호출 시 json-schema로 인자 검증 → 값 넘기기 → 실행 → 결과 반환

#### 예시 그림
```
[add(num1, num2)]  등록 -->  Tool(name='add', ...)  --(name: 'add')-->  ToolManager
                             |
                   ToolManager.call_tool('add', {'num1': 1, 'num2': 2})
                             |
                  ---> 실제 함수 실행 & 결과 반환
```

### ResourceManager의 유연함

- 단순 텍스트, 파일, HTTP 응답, 폴더내 파일목록 등 다양한 리소스를 한 지정좌표(uri)에 등록
- 정적 리소스와 동적(템플릿) 리소스 둘 다 지원  
  예) `/files/my.txt` → 실제 파일 /files/my.txt 읽어서 응답

### PromptManager의 편리함

- 함수 자체가 프롬프트의 정의 (입력 인자→템플릿 문자열 출력)
- 이름만 지정해두면 클라이언트에서 편리하게 재사용 가능
- 인자 타입과 설명, 필수 여부 등도 자동화

---

## 마무리 (Wrap-up)

- **ToolManager, ResourceManager, PromptManager** 세 가지 매니저는 MCP 서버 내 "가장 자주 쓰이는 인터페이스"입니다.
- 각각 "서버에 붙여둔 기능(함수), 데이터(리소스), 프롬프트(질문/명령 양식)"를 한데 모아서 관리합니다.
- 개발자는 복잡한 통신·직렬화 걱정 없이,  
  단순히 함수를 등록하거나 파일을 추가하거나 프롬프트를 만들어두면  
  서버 API로 자연스럽게 외부에 노출됩니다.

**핵심:**  
이 매니저들이 있어야만, MCP 서버가 좀 더 "스마트하고 확장 가능한" 서비스 플랫폼이 됩니다.

다음 장에서는 "이 매니저들과 클라이언트/서버가 실제로 통신할 때 사용되는 메시지 구조"를 배웁니다!  
(→ [3장: MCP 메시지/통신 시스템(SessionMessage 등)] 으로 이동)

---