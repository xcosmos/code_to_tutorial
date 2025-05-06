# Chapter 2: 피드백(Feedback) 생성 모듈

---

## 동기(Motivation)

여러분이 친구에게 "우주에 대해 알려줘"라고 묻는다고 생각해 봅시다. 친구는 이렇게 물을 수 있습니다.  
_"우주에서 어떤 점이 궁금한데?"_

즉, 아주 넓은 질문을 받으면, 더 뚜렷하고 구체적인 내용을 알기 위해 다시 질문—즉, **후속 질문**—을 던지는 것이 자연스럽습니다.  
이렇게 해야야 친구도 도와줄 수 있고, 질문한 사람도 진짜 원하는 답을 얻을 가능성이 높아집니다.

AI에게 연구를 부탁할 때도 마찬가지로, 처음 질문이 막연하면 조금 더 뾰족한 추가 질문이 필요합니다.  
그래야 AI도 원하는 정보를 알맞게 수집할 수 있습니다.  
이 역할을 하는 핵심이 바로 **피드백(Feedback) 생성 모듈**입니다.

---

## 핵심 아이디어(Key Ideas)

- 사용자의 애매한 질문을 듣고, 더 정확한 답을 찾기 위한 **후속 질문**을 자동으로 만들어줍니다.
- 마치 인터뷰어(기자)처럼 "이 부분이 궁금하신 건가요?", "그중에서도 어떤 게 제일 알고 싶으신가요?"라고 물어봅니다.
- 연구 전체 과정의 출발점! 한마디로, 좋은 **출발선 다듬기** 역할입니다.

---

## 코드

코드는 `step1_feedback/feedback.py` 파일에 들어 있습니다. 주요 함수는 `generate_feedback`입니다.
아래에서 가장 중요한 부분을 순서대로 나눠 보고 설명합니다.

---

### 1. 기본 구조와 준비물

```python
from typing import List
from utils import JSON_llm, system_prompt
from pydantic import BaseModel

class FeedbackResponse(BaseModel):
    questions: List[str]
```

**설명:**  
- 필요한 도구들(import)을 불러옵니다.  
- `FeedbackResponse`는 결과가 어떻게 생겼는지(질문 리스트만 있는 결과)를 알려주는 구조입니다.

---

### 2. 함수 정의와 역할 주석

```python
"""연구 방향을 명확히 하기 위한 후속 질문을 생성합니다."""
def generate_feedback(query: str, client, model: str, max_feedbacks: int = 3) -> List[str]:
```

**설명:**  
- 이 함수가 하는 일: 사용자의 질문(`query`)을 받아서, **후속 질문 최대 3개**까지 뽑아주는 함수  
- `client`와 `model`은 어떤 AI를 쓸지 정하는 정보이고, `max_feedbacks`는 후속 질문을 몇 개까지 만들지 제한합니다.

---

### 3. 프롬프트 만들기 (LLM에게 보내는 요청문)

```python
prompt = f"""
Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of ${max_feedbacks} questions, but feel free to return less if the original query is clear.
ask the follow up questions in korean
<query>${query}</query>`
"""
```

**설명:**  
- **프롬프트(prompt)**란?  
  AI에게 "어떻게 답을 해줘!"라고 주는 상세한 설명문입니다.
- 여기서는:
    - "다음 사용자의 질문에 대해, 연구 방향을 명확하게 할 후속 질문을 해주세요."
    - "최대 3개만, 질문이 이미 명확하다면 적게(혹은 아예 없음) 만들어도 돼."
    - "꼭 한국어로!"
- 즉, AI가 꼭 필요한 만큼의 후속 질문만 똑똑하게 만들어 주기를 기대합니다.

---

### 4. LLM 호출 및 JSON 변환

```python
response = JSON_llm(
    prompt, 
    FeedbackResponse, 
    client, 
    system_prompt=system_prompt(), 
    model=model
)
```

**설명:**  
- `JSON_llm`:  
  이 함수는 위에서 만든 프롬프트(prompt)와 정해진 결과 구조(FeedbackResponse)를 가지고,  
  실제 AI에게 질문을 보내고, 결과를 받아옵니다.
- AI가 준 답이 JSON(딕셔너리 형태)으로 오게 만듭니다.

---

### 5. 결과 처리 및 예외 처리

```python
try:
    if response is None:
        print("오류: JSON_llm이 None을 반환했습니다.")
        return []
    questions = response.questions
    print(f"주제 '{query}'에 대한 후속 질문 {len(questions)}개 생성됨")
    print(f"생성된 후속 질문: {questions}")
    return questions
except Exception as e:
    print(f"오류: JSON 응답 처리 중 문제 발생: {e}")
    print(f"원시 응답: {response}")
    print(f"오류: 쿼리 '{query}'에 대한 JSON 응답 처리 실패")
    return []
```

**설명:**  
- 정상적으로 답변이 오면, 그 질문 리스트(`questions`)를 **리턴**합니다.
- 만약 AI 응답에 문제가 있거나, 결과 형식이 이상하거나, 에러가 나면:
    - 에러 메시지를 출력하고
    - 빈 리스트(`[]` = 질문 없음)를 돌려보냅니다.

---

## 단계 전체 흐름 정리

1. 사용자 질문 → 
2. **generate_feedback** 함수 호출 →
3. AI에게 "후속 질문 만들어줘!"라고 프롬프트 보냄 →
4. JSON 형식으로 후속 질문 리스트를 받음 →
5. 후속 질문 표시/사용

이 과정을 한마디로 하면,  
**"당신의 질문을 더 좋은 연구 주제로 다듬어줄 인터뷰!"** 입니다.

---

## 마무리

피드백(Feedback) 생성 모듈은,  
마치 꼼꼼한 연구 지도교수나 인터뷰어처럼  
**"어떤 점이 더 궁금하세요?"**  
라고 물어봐 주는 역할입니다.

이 과정을 거치면  
- 애매하고 넓은 질문이
- 좀 더 **명확하고 파고들기 쉬운 주제**로 바뀌고,
- 전체 AI 딥리서치(deep research) 과정이 훨씬 잘 진행됩니다.

다음 장에서는 이렇게 다듬어진 질문을 바탕으로,  
실제로 **웹에서 지식을 어떻게 넓고 깊게 탐색**하는지 알아보겠습니다!