# AI 튜토리얼 생성기

AI를 활용하여 코드베이스를 자동으로 튜토리얼로 변환하는 프로젝트입니다.
- 내가 더 공부해보고 싶은 코드베이스의 링크, 프로젝트 이름, 튜토리얼 언어 및 챕터 수 입력 후 "튜토리얼 생성" 버튼 클릭
- 각 장별로 튜토리얼이 생성되고 스트림릿에서 바로 확인하거나 마크다운 파일로 다운로드 가능

(예시 화면)
![image](https://github.com/user-attachments/assets/b2b31861-d48d-4c22-acc5-b76924adce89)

* https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge 의 주요 내용을 기반으로 내용을 간소화하고 Streamlit으로 구현한 프로젝트입니다.


---

## 요구사항

* 주요 패키지: `pyyaml`, `streamlit`, `openai`, `requests`, `python-dotenv`

```bash
pip install pyyaml streamlit openai requests python-dotenv
```

---

## OpenAI API 키 설정

이 프로젝트는 OpenAI API를 사용합니다.

1. [OpenAI 웹사이트](https://platform.openai.com/api-keys)에서 API 키를 발급받으세요.
2. 프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래와 같이 작성하세요:

```
OPENAI_API_KEY=your-api-key-here
```

---

## 설치 및 실행 방법

### UV 환경 (권장)

```bash
# 메인 로직 실행
uv run main.py

# Streamlit UI 실행
uv run streamlit run streamlit_ui.py
```

---

### venv 환경

```bash
# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화
# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 의존성 설치
pip install pyyaml streamlit openai requests python-dotenv

# 메인 로직 실행
python main.py

# Streamlit UI 실행
streamlit run streamlit_ui.py
```

---

