# Chapter 2: 연구 파이프라인의 엔트리포인트 (main.py)

## 왜 main.py가 중요할까요? (Motivation)

앞에서 우리는 LLM 헬퍼 함수가 AI와 ‘대화’를 돕는 도구라는 것을 배웠습니다. 그런데 이런 여러 도구들이 각각 제 역할을 하려면, 누군가 전체 과정을 **감독**하고, **순서대로** 실행시켜야 합니다. main.py가 바로 이 역할을 맡고 있습니다.

쉽게 말하면, main.py는 딥리서치 프로젝트의 ‘감독자’이자 ‘지휘자’입니다. 오케스트라에서 각 악기(함수, 도구)가 제대로 연주할 수 있도록, main.py가 무대를 세팅하고 **연구 전체 흐름**을 조율합니다.

## 주요 아이디어 (Key Ideas)

- **엔트리포인트(entrypoint):** main.py는 프로그램 실행의 출발점, 즉 첫 단추 역할을 합니다.
- **프로세스 관리:** 연구의 ‘질문 → 조사 → 보고서 생성’ 흐름이 순서대로 진행되도록 각 단계의 함수를 차례차례 호출해줍니다.
- **자동화:** 한 번 실행하면, 사용자의 최소 입력만으로 전체 연구 프로세스가 자동으로 굴러갑니다.
- **코어 로직:** 사용자 입력, 중간 결과 관리, 각 단계 함수 호출, 최종 보고서 저장까지의 ‘핵심 시나리오’가 이 안에 담겨 있습니다.

---

## main.py 살펴보기 (Code)

이제 main.py 코드를 한 부분씩 나눠서 살펴봅시다.

---

### 1. 준비 단계: 라이브러리와 함수 불러오기

```python
import os
from openai import OpenAI
from step1_feedback.feedback import generate_feedback
from step2_research.research import deep_research
from step3_reporting.reporting import write_final_report
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수를 불러옵니다.
```

**설명:**  
연구를 위해 AI와 대화하고, 피드백(질문 생성), 리서치, 보고서 생성에 필요한 함수들을 가져옵니다.  
또한 `.env` 파일에서 API 키 등 중요한 정보를 읽어옵니다.

---

### 2. 메인 함수 만들기

```python
def main():
```

**설명:**  
파이썬 프로그램의 ‘시작 지점’인 `main()` 함수를 정의합니다.  
(맨 아래에서 `if __name__ == "__main__": main()` 코드가 실제 실행을 담당합니다.)

---

### 3. 사용자로부터 연구 질문 입력받기

```python
    query = input("어떤 주제에 대해 리서치하시겠습니까?: ")
```

**설명:**  
사용자에게 ‘연구하고 싶은 주제나 궁금증’을 키워드나 문장 형태로 입력받습니다.  
예) ‘전기차 배터리의 미래 전망’, ‘미드저니와 스테이블디퓨전의 차이’

---

### 4. 사용할 AI 모델 선정

```python
    feedback_model = "gpt-4o-mini"
    research_model = "gpt-4o"
    reporting_model="o1-mini"
    client = OpenAI()
```

**설명:**  
각 단계별로 사용할 AI 모델을 골라줍니다.  
(필요에 따라 더 빠른, 저렴한, 혹은 더 똑똑한 모델로 변경 가능)

---

### 5. 1단계: 후속 질문 자동 생성

```python
    print(f"------------------------------------------1단계: 추가 질문 생성----------------------------------------------------")
    feedback_questions = generate_feedback(query, client, feedback_model, max_feedbacks=3)
    answers = []
    if feedback_questions:
        print("\n다음 질문에 답변해 주세요:")
        for idx, question in enumerate(feedback_questions, start=1):
            answer = input(f"질문 {idx}: {question}\n답변: ")
            answers.append(answer)
    else:
        print("추가 질문이 생성되지 않았습니다.")
```

**설명:**  
- AI가 연구 주제를 더 똑똑하게, 구체적으로 파악할 수 있도록 **후속 질문**을 자동으로 만들어줍니다.  
- 사용자는 이 질문들에 답하면서 스스로도 생각을 정리하고, 리서치 방향성을 잡게 됩니다.

---

### 6. 질문과 답변 모으기

```python
    combined_query = f"초기 질문: {query}\n"
    for i in range(len(feedback_questions)):
        combined_query += f"\n{i+1}. 질문: {feedback_questions[i]}\n"
        combined_query += f"   답변: {answers[i]}\n"
        
    print("최종질문 : \n")
    print(combined_query)
```

**설명:**  
- 초기 질문 + 후속 질문 + 각각의 답변을 **하나로 합쳐서**, 이후 단계(심층 조사)에 넘깁니다.  
- 이렇게 해야 AI가 더 풍부한 맥락을 이해하고, 좋은 결과를 내놓을 수 있습니다.

---

### 7. 연구 범위와 깊이 입력

```python
    try:
        breadth = int(input("연구 범위를 입력하세요 (예: 2): ") or "2")
    except ValueError:
        breadth = 2
    try:
        depth = int(input("연구 깊이를 입력하세요 (예: 2): ") or "2")
    except ValueError:
        depth = 2
```

**설명:**  
- 해당 연구가 ‘얼마나 넓고 깊게’ 진행될지 설정합니다.  
- **범위(breadth):** 조사할 세부 항목 개수  
- **깊이(depth):** 각 항목마다 얼마나 깊이 파고들지  
- 초보자는 기본값(2)을 쓰면 됩니다.

---

### 8. 2단계: AI를 활용한 딥리서치 실행

```python
    print(f"------------------------------------------2단계: 딥리서치----------------------------------------------------")
    research_results = deep_research(
        query=combined_query,
        breadth=breadth,
        depth=depth,
        client=client,
        model=research_model
    )
```

**설명:**  
- 이제 본격적으로 AI가 각종 자료를 조사하고, 핵심 학습 포인트(리서치 결과)를 뽑아냅니다.

---

### 9. 조사 결과 출력

```python
    print("\n연구 결과:")
    for learning in research_results["learnings"]:
        print(f" - {learning}")
```

**설명:**  
리서치 결과로 AI가 정리한 주요 인사이트(핵심 내용)들을 출력합니다.

---

### 10. 3단계: 최종 결과보고서 작성

```python
    print(f"------------------------------------------3단계: 보고서 작성----------------------------------------------------")

    report = write_final_report(
        prompt=combined_query,
        learnings=research_results["learnings"],
        visited_urls=research_results["visited_urls"],
        client=client,
        model=reporting_model
    )
```

**설명:**  
- 딥리서치 결과를 바탕으로 최종 보고서를 자동으로 완성합니다.  
- 논리적, 깔끔한 텍스트 보고서로 저장됩니다.

---

### 11. 보고서 저장 및 안내

```python
    print("\n최종 보고서:\n")
    print(report)
    with open("output/output.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n보고서가 output/output.md 파일에 저장되었습니다.")
```

**설명:**  
최종 결과를 터미널(콘솔)에 보여주고,  
`output/output.md` 파일로 저장합니다.  
이제 언제든 파일로 내용을 확인하고, 공유할 수도 있습니다.

---

## 마무리 (Wrap-up)

이번 장에서는 **main.py**가 딥리서치 프로젝트에서 어떻게 **전체 연구 흐름을 관리**하고,  
각 단계(질문 생성 → AI 리서치 → 보고서 생성)를 자동으로 실행‧연결해주는지 알아봤습니다.

main.py는 _‘하나의 파일 실행으로 딥리서치 자동화’_ 를 실현하는 **핵심 스크립트**입니다.  
이 파일을 이해하면, 연구 자동화의 큰 그림이 그려질 것입니다.

---

다음 장에서는, 본격적으로 **후속질문 생성기(generate_feedback)**가 어떻게 작동하는지 자세히 살펴봅니다.  
이 파트는 연구의 방향을 명확하게 잡는 데 아주 중요한 단계입니다! 🚀