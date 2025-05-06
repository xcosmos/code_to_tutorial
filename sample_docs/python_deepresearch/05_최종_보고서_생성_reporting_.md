# Chapter 5: 최종 보고서 생성(reporting)

앞의 단계들에서는 질문을 세분화하고, 다양한 방법으로 정보를 수집했으며, 외부 자료까지 연결하여 연구를 진행했습니다. 이번 마지막 챕터에서는 그 모든 결과물을 한데 모아, 보기 쉬운 "최종 보고서"로 만드는 과정을 다룹니다.

---

## 동기부여: 왜 보고서가 중요한가요?

연구라는 것은, 단순히 정보를 모으는 데서 끝나지 않습니다. 내 머릿속에만 정리가 되어 있는 것이 아니라, 남이 읽어도 이해할 수 있게 잘 정리된 문서가 필요하지요.  
보고서는 마치 탐험가가 발견한 보물을 지도에 그려 다른 사람에게 알려주는 역할을 합니다.  
내가 무엇을 배우고, 어디서 어떤 정보를 참고했는지를 체계적으로 남겨두면, 나중에 내가 다시 참조하거나 다른 사람과 공유하기도 훨씬 편합니다.

---

## 핵심 아이디어

- **자동 문서화**: 지금까지 모은 학습 내용, 참고한 출처(URL)들을 자동으로 정리해서, 보기 쉬운 마크다운 파일로 만듭니다.
- **논문 작성 도우미**: 번거로운 편집 없이, 클릭 한 번으로 체계적인 리포트가 완성됩니다.
- **출처 명시**: 어떤 정보를 어디서 얻었는지 출처까지 꼼꼼히 남깁니다.

이 기능의 핵심은 `step3_reporting/reporting.py`의 `write_final_report` 함수가 담당합니다.

---

## 코드 분해 및 설명

**1. main.py의 최종 보고서 생성 부분**

`main.py`에서 연구가 모두 끝난 후, 아래 코드가 실행됩니다.

```python
report = write_final_report(
    prompt=combined_query,
    learnings=research_results["learnings"],
    visited_urls=research_results["visited_urls"],
    client=client,
    model=reporting_model
)
```

이 부분은 지금까지 모은 모든 정보(프롬프트, 연구 학습 내용, 방문한 URL)를 `write_final_report` 함수에 넘겨줍니다.  
그리고 아래처럼 최종적으로 나온 보고서를 파일에 저장합니다.

```python
with open("output/output.md", "w", encoding="utf-8") as f:
    f.write(report)
print("\n보고서가 output/output.md 파일에 저장되었습니다.")
```

**이 부분의 의미:**  
- 사용자가 직접 정리할 필요 없이 자동으로 보고서가 정돈되어 파일로 저장됩니다.
- 파일은 `output/output.md`로 저장되니, 바로 열어볼 수 있습니다.

---

**2. step3_reporting/reporting.py: 보고서 생성 함수**

이제 실제로 보고서를 만들어주는 함수의 내부를 살펴봅니다.

```python
def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    client,
    model: str,
) -> str:
    # ... (중략)
    learnings_string = ("\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])).strip()[:150000]

    user_prompt = (
        f"사용자가 제시한 다음 프롬프트에 대해, 러서치 결과를 바탕으로 최종 보고서를 작성하세요. "
        f"마크다운 형식으로 상세한 보고서(6,000자 이상)를 작성하세요. "
        f"러서치에서 얻은 모든 학습 내용을 포함해야 합니다:\n\n"
        f"<prompt>{prompt}</prompt>\n\n"
        f"다음은 리서치를 통해 얻은 모든 학습 내용입니다:\n\n<learnings>\n{learnings_string}\n</learnings>"
    )
    sys_prompt = system_prompt()
    if sys_prompt:
        user_prompt = f"{sys_prompt}\n\n{user_prompt}"

    try:
        report = llm_call(user_prompt, model, client)
        urls_section = "\n\n## 출처\n\n" + "\n".join(f"- {url}" for url in visited_urls)
        return report + urls_section
    except Exception as e:
        print(f"Error generating report: {e}")
        return "Error generating report"
```

### 각 부분 설명

- **learnings_string**  
  여러 개로 따로 저장된 "학습 내용"을 하나의 큰 문자 덩어리로 합칩니다.  
  `<learning> ... </learning>` 태그로 감싸 정리하기 쉽도록 합니다.

- **user_prompt**  
  AI(LLM)에게 "어떻게 보고서를 써달라"고 요청하는 특별한 지시문을 만듭니다.  
  - 사용자의 질문/프롬프트
  - 학습 내용 전체  
  를 포함해서 AI가 마크다운 형식으로 논문처럼 길고 정돈된 보고서를 써주도록 시킵니다.

- **system 프롬프트**  
  보조 시스템 메시지가 있으면 앞에 추가합니다.

- **llm_call(user_prompt, model, client)**  
  실제로 AI 모델(GPT 등)에게 보고서 작성을 시킵니다.  
  모델은 입력받은 자료와 지시대로 출력을 만들어냅니다.

- **출처 붙이기**  
  보고서가 만들어진 뒤, 마지막 부분에  
  ```
  ## 출처
  - [url1]
  - [url2]
  ```
  와 같이, 참고했던 모든 URL을 목록으로 추가합니다.

---

## 전체 흐름 요약

1. 모든 연구가 끝난 후, 학습 내용과 방문한 웹 주소가 모입니다.
2. AI에게 "이걸 참고해서 체계적이고 보기 좋은 마크다운 보고서를 써달라"고 명령합니다.
3. AI가 논문처럼 본문을 만들고, 그 아래에 참고자료 목록(출처)이 붙습니다.
4. 이 결과물이 파일(`output/output.md`)로 저장되어 최종 산출물이 됩니다.

---

## 마치며

이번 챕터에서는 그동안의 연구 활동이 한 편의 보고서로 완성되는 과정을 살펴봤습니다.  
이 과정을 마치면, 아래와 같은 점이 편리해집니다.

- 누구나 이해할 수 있는 형태로 연구 결과를 남길 수 있습니다.
- 논문, 과제, 리서치 요약 등 다양한 분야에 바로 활용할 수 있습니다.
- 출처가 깔끔하게 남아 신뢰성과 활용도가 높습니다.

이로써, `python deep research` 튜토리얼의 모든 핵심 단계를 마무리합니다.  
챕터 1~5의 흐름을 전체적으로 반복해 본다면, 스스로 응용 프로젝트에도 도전할 수 있을 것입니다!

고생 많으셨고, 멋진 리서치 생활이 되길 바랍니다. 🚩