# Chapter 4: Firecrawl 검색 연동

---

## 동기 (Motivation)

딥리서치 프로젝트에서 가장 중요한 것은 **최신 정보**를 신속하게 수집하는 것입니다. 하지만, 우리가 웹에서 정보를 직접 찾으려면 검색 포털을 일일이 방문해서 복사·붙여넣기를 반복해야 합니다.  
이러한 과정을 자동으로 대신해주는 **검색 엔진 연동**이 필요합니다.

딱 맞는 도구가 바로 **Firecrawl**입니다!  
Firecrawl은 구글, 네이버, 뉴스 사이트 등에 직접 검색을 수행하고, 결과를 받아서 정돈해줍니다.  
여러분이 어릴 적 **"정보를 모아 오는 로봇"**을 상상해 봤다면, 바로 이 Firecrawl이 여러분 곁의 똑똑한 R&D(Robot & Data) 로봇 역할을 합니다.

---

## 핵심 아이디어 (Key Ideas)

- **자동화된 검색**: 사용자가 주제를 주면 Firecrawl이 대신 검색하고, 결과(웹페이지 제목·내용·설명·URL 등)를 긁어옵니다.
- **코드 안에 외부정보 연결하기**: 파이썬 코드에서 외부(실제 인터넷) 데이터를 다리처럼 가져올 수 있습니다.
- **쉽게 재사용**: 함수만 부르면, 복잡한 웹 크롤러 없이 최신 결과가 한 번에!

---

## 실제 코드 (Code) — Firecrawl 검색 호출

아래는 실제로 Firecrawl을 활용하여 검색하는 코드의 중요한 부분입니다.  
(프로젝트의 `step2_research/research.py` 파일과 `test.py`에 구현되어 있어요.)

```python
from firecrawl import FirecrawlApp

def firecrawl_search(query: str, timeout: int = 15000, limit: int = 5):
    # Firecrawl 검색 API를 호출하여 결과를 반환
    try:
        app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY", ""))
        response = app.search(
            query=query,
            params={"timeout": timeout, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}}
        )
        return response.get("data", [])
    except Exception as e:
        print(f"Firecrawl 검색 오류: {e}")
```

실제로 테스트하면 이렇게 출력됩니다:

```
결과 1:
제목: 아침 운동의 신체적 이점
URL: https://example.com/health/article
본문: ... (웹사이트에서 긁어온 요약 내용 또는 본문 일부)
설명: ... (검색결과 요약 설명)
```

---

## 각 코드 단계별 풀이 (Step-by-step Explanation)

### 1. FirecrawlApp 객체 만들기

```python
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY", ""))
```

- Firecrawl 검색을 쓰려면 "API 키"가 필요해요.  
- FirecrawlApp은 "검색을 담당하는 우리만의 작은 로봇"이라고 생각하세요.

### 2. 검색을 실제로 실행

```python
response = app.search(
    query=query,
    params={"timeout": timeout, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}}
)
```

- 어떤 키워드로 검색할지를 query로 넣습니다.
- timeout은 "얼마나 오래 기다릴지"(ms 단위), limit은 "몇 개 결과를 받을지"입니다.
- scrapeOptions로 "결과를 마크다운 형식으로 받기"를 지정합니다.  
  (마크다운은 웹텍스트를 쉽게 다루는 문서 양식입니다)

### 3. 데이터 꺼내 쓰기

```python
return response.get("data", [])
```

- 실제 검색 결과(리스트, 즉 여러 개의 결과)가 data 키 아래에 담겨 나옵니다.
- 각각의 결과에는 **제목(title), URL, 본문(markdown), 설명(description)** 정보가 있어요.

### 4. 오류 처리

```python
except Exception as e:
    print(f"Firecrawl 검색 오류: {e}")
```

- 인터넷 검색은 예기치 못한 네트워크 오류가 있을 수 있으니, 항상 조심해서 다룹니다.

---

## 일상 비유로 이해하기 (Analogy)

손수 도서관에 가서 자료를 찾는 사람과,  
"이 주제로 쫙 조사해서 자료 요약해 와줘!" 하고 믿을 만한 친구에게 부탁하는 사람을 생각해보세요.

Firecrawl은 우리 코드의 **부지런한 조사원 친구**입니다.
검색 결과를 대신 찾아오고, 그 내용을 알기 쉬운 포맷(마크다운)으로 정리해줍니다.

---

## 활용 예시 및 테스트

`test.py` 파일의 테스트 예시를 보면,  
Firecrawl 검색 결과가 잘 출력되는 모습을 확인할 수 있습니다.

**실제 실행하면 아래와 같은 식으로 결과를 받습니다:**

```
검색어 '아침 운동의 신체적 이점'에 대한 결과:

결과 1:
제목: 왜 아침 운동이 몸에 좋을까요?
URL: https://www.healthsite.com/morning-benefits
본문: ... (웹사이트 내용 일부)
설명: ... (핵심 요약)
```

이렇게 파이썬 코드만 짧게 실행해도,  
**실시간 최신 자료를 내 코드로 바로 끌어올 수 있는 것**이 정말 큰 장점입니다!

---

## 마무리 (Wrap-up)

이 챕터에서는 딥리서치 프로젝트의 똑똑한 **검색 연동 도우미 Firecrawl**에 대해 배웠습니다.

- Firecrawl을 이용하면 다양한 검색엔진에서 최신 정보를 자동으로 받아올 수 있습니다.
- 파이썬 코드 속에서 손쉽게 검색 결과(제목, URL, 본문 등)를 다룰 수 있습니다.
- 이 과정을 통해 딥리서치의 뇌는 "외부 정보와 연결된 넓은 연구자 네트워크"처럼 확장됩니다.

다음 장에서는 이렇게 수집된 정보들을 어떻게 멋진 **최종 연구 보고서**로 엮는지 알아봅니다! 🚀

---