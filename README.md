반영해서 더 정리된 버전으로 아래와 같이 개선했습니다.

* 아이콘 제거
* OpenAI API 키 설정을 사용법 섹션보다 **위**로 이동

---

# AI 튜토리얼 생성기

AI를 활용하여 코드베이스를 자동으로 튜토리얼로 변환하는 프로젝트입니다.
메인 로직과 Streamlit UI는 `uv` 또는 `venv` 환경에서 실행할 수 있습니다.

---

## 요구사항

* Python 3.7 이상
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

