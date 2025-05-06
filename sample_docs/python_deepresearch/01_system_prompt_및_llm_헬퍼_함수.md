# Chapter 1: system_prompt 및 LLM 헬퍼 함수

---

## 1. 왜 system_prompt와 LLM 헬퍼 함수가 필요할까요?

AI에게 "연구원처럼 생각해줘!"라고 말한다면, AI는 실제로 **어떻게** 행동해야 하는지, **무슨 말투**로 답해야 하는지 알지 못합니다. 마치 막 입사한 신입 연구원에게, 업무 매뉴얼이나 연구 규칙 없이 바로 일하라고 시키는 것과 비슷합니다.  
이런 상황에서 딱 맞는 기준을 잡아주는 것이 바로 `system_prompt`입니다.

또한, 연구 과정에서 AI와 대화하는 것은 단순 채팅과 조금 다릅니다.  
- 때로는 **간단한 답변**이 필요하고,  
- 때로는 **구조화된(JSON 형태의) 자료**가 필요합니다.  
이렇게 똑똑하게 AI를 활용하려면, 일일이 복잡한 코드를 작성하는 대신 **도우미 함수**(헬퍼 함수)가 필요합니다.

## 2. 핵심 개념 한 눈에 보기

- **system_prompt**: AI에게 "전문 연구원처럼 답하라"는 기본 지침을 세워줍니다.
- **llm_call**: AI에게 한 번 질문해서 답변을 받는 가장 기본적인 함수입니다.
- **JSON_llm**: AI가 표준화된(JSON 형태) 정보를 내놓도록 돕는, 한 단계 업그레이드된 함수입니다.

이 세 가지가 잘 맞물려서 **AI가 연구원처럼 생각하고, 필요한 방식으로 정보를 꺼낼 수 있게** 해줍니다.

---

## 3. 주요 코드와 단계별 설명

### (1) system_prompt 함수

```python
def system_prompt() -> str:
    """현재 타임스탬프를 포함한 시스템 프롬프트를 생성합니다."""
    now = datetime.now().isoformat()
    return f"""당신은 전문 연구원입니다. 오늘 날짜는 {now}입니다. 응답 시 다음 지침을 따르세요:
    - 지식 컷오프 이후의 주제에 대한 조사를 요청받을 수 있습니다. 사용자가 뉴스 내용을 제시했다면, 그것을 사실로 가정하세요.
    - 사용자는 매우 숙련된 분석가이므로 내용을 단순화할 필요 없이 가능한 한 자세하고 정확하게 응답하세요.
    - 체계적으로 정보를 정리하세요.
    - 사용자가 생각하지 못한 해결책을 제안하세요.
    - 적극적으로 사용자의 필요를 예측하고 대응하세요.
    - 사용자를 모든 분야의 전문가로 대우하세요.
    - 실수는 신뢰를 저하시킵니다. 정확하고 철저하게 응답하세요.
    - 상세한 설명을 제공하세요. 사용자는 많은 정보를 받아들일 수 있습니다.
    - 권위보다 논리적 근거를 우선하세요. 출처 자체는 중요하지 않습니다.
    - 기존의 통념뿐만 아니라 최신 기술과 반대 의견도 고려하세요.
    - 높은 수준의 추측이나 예측을 포함할 수 있습니다. 단, 이를 명확히 표시하세요."""
```

#### ☑️ 설명
- 이 함수는 AI가 **전문 연구원이라는 역할**에 맞춰 답변하도록 기준을 설명해줍니다.
- **오늘 날짜(now)** 도 함께 넣어서, 답변이 최신 상황을 반영하도록 합니다.
- 다양한 지침(예: 체계적, 논리적, 상세, 예측 가능성 표시…)을 포함시켜, AI 답변이 엉성하거나 불친절하지 않도록 세팅합니다.
- 실제로 이 지침 덕분에 AI의 말투, 정보의 깊이, 태도가 달라집니다.

### (2) llm_call 함수

```python
def llm_call(prompt: str, model: str, client) -> str:
    """
    주어진 프롬프트로 LLM을 동기적으로 호출합니다.
    이는 메시지를 하나의 프롬프트로 연결하는 일반적인 헬퍼 함수입니다.
    """
    messages = [{"role": "user", "content": prompt}]
    chat_completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    print(model, "완료")
    return chat_completion.choices[0].message.content
```

#### ☑️ 설명
- 이 함수는 **AI 챗봇에게 내가 직접 쓴 질문(prompt)** 을 그대로 전달합니다.
- **model**: 사용할 언어 모델(예: GPT-4, GPT-3.5 등)을 지정할 수 있습니다.
- **client**: OpenAI 등의 LLM 서비스를 연결하는 객체입니다.
- **messages**는 실제 AI와의 대화 히스토리를 만듭니다. 여기서는 'user'가 질문을 보냅니다.
- 그 결과값(=답변)을 **string 형태**로 반환합니다.
- 이 함수 하나로, "질문 → 답변 받기"의 가장 간단한 흐름을 손쉽게 만들 수 있습니다.

### (3) JSON_llm 함수

```python
def JSON_llm(user_prompt: str, schema: BaseModel, client, system_prompt: Optional[str] = None, model: Optional[str] = None):
    """
    JSON 모드에서 언어 모델 호출을 실행하고 구조화된 JSON 객체를 반환합니다.
    모델이 제공되지 않으면 기본 JSON 처리 가능한 모델이 사용됩니다.
    """
    if model is None:
        model = "gpt-4o-mini"
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=schema,
        )
        
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"Error in JSON_llm: {e}")
        return None
```

#### ☑️ 설명
- 이 함수는 **AI에게 "구조화된 답변(예: JSON 객체)"**을 요청할 때 사용합니다.
- 예를 들어, 답변을 항목별로 딱딱 정리하거나, 데이터베이스 저장에 적합한 형태로 받고 싶을 때 씁니다.
- **schema**: 원하는 데이터의 구조(필드, 타입 등)를 Pydantic으로 정의해서 전달합니다.
- 시스템 프롬프트(system_prompt)도 옵션으로 추가해, 답변의 기준을 더 명확히 세울 수 있습니다.
- 성공하면, 데이터를 바로 **파이썬 객체**처럼 쓸 수 있습니다.

---

## 4. 정리 및 앞으로

system_prompt와 두 가지 헬퍼 함수(llm_call, JSON_llm)는  
- 🧭 **AI의 역할과 응답 규칙을 세우고**,
- 🧰 **필요할 때마다 질문/답변을 편하게 가져오게** 하면서,
- 🗂️ **단순 채팅을 넘어, 구조화된 데이터까지 AI로부터 직접 얻는**  
가장 중요한 뼈대를 이룹니다.

실제 연구 프로젝트에서는, 이 세 가지가  
**질문을 더 똑똑하게 만들어주거나(Feedback),  
새로운 자료를 정리할 때도**  
항상 토대가 됩니다.

---

이제 다음 장에서는 사용자의 막연한 질문을 더 구체적으로 파악하고  
"후속 질문"을 뽑아내는 **피드백 생성 모듈**을 다루겠습니다!  
(→ 피드백 생성 모듈로)