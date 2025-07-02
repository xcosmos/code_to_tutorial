import streamlit as st
from pathlib import Path
import io
import zipfile
import logging

# Logger setup
g_logger = logging.getLogger(__name__)

def setup_logging(log_path: Path = Path("debug.log")) -> None:
    """
    Configure file logging.
    """
    try:
        handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')  # 'a' mode for append
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        g_logger.addHandler(handler)
        g_logger.setLevel(logging.INFO)
        g_logger.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise

setup_logging()

# Constants
DOCS_DIR = Path("streamlit_docs")

# Import your core functions
from main import fetch_github_repo, extract_abstractions, generate_tutorials

def main():
    st.set_page_config(page_title="📘 AI 튜토리얼 생성기", layout="wide")

    # Sidebar 토글 상태 초기화
    if 'sidebar_visible' not in st.session_state:
        st.session_state.sidebar_visible = True

    # 토글 버튼 추가
    if st.button('Toggle Sidebar', help='클릭하여 사이드바를 토글합니다'):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible

    # 사이드바 표시/숨김 제어
    if st.session_state.sidebar_visible:
        with st.sidebar.form(key="config_form"):
            st.title("📘 AI 튜토리얼 생성기")
            repo_url      = st.text_input("GitHub 저장소 URL", value="https://github.com/marcel-kanter/python-canopen")
            token         = st.text_input("GitHub 토큰 (선택)", type="password")
            project_name  = st.text_input("프로젝트 이름", value="My Project")
            language      = st.selectbox("언어", options=["korean", "english"], index=0)
            max_n         = st.number_input("챕터 수", min_value=1, max_value=10, value=6)
            generate_btn  = st.form_submit_button("튜토리얼 생성")

        if generate_btn:
            try:
                # 1. GitHub에서 코드 가져오기
                files = fetch_github_repo(repo_url, token)
                
                # 2. 코드의 핵심 개념 추출
                abstractions = extract_abstractions(files, project_name, language, max_n)
                
                # 3. 튜토리얼 생성
                output_dir = Path("streamlit_docs")
                tutorial_paths = generate_tutorials(abstractions, files, output_dir, project_name, language, repo_url)
                
                st.success("튜토리얼이 성공적으로 생성되었습니다!")
                
                # 생성된 튜토리얼 파일 목록 표시
                st.subheader("생성된 튜토리얼 파일들")
                for path in tutorial_paths:
                    st.write(f"- {Path(path).name}")
                    
            except Exception as e:
                st.error(f"에러 발생: {str(e)}")
                g_logger.error(f"에러 발생: {str(e)}")

        st.sidebar.title("📚 생성된 튜토리얼")
        md_files = sorted(DOCS_DIR.glob("*.md"))

        if md_files:
            # Replace underscores with spaces in sidebar labels
            selected_path = st.sidebar.radio(
                "챕터 선택",
                options=md_files,
                format_func=lambda path: path.stem.replace("_", " ")
            )
            content = selected_path.read_text(encoding="utf-8")
            st.markdown(content, unsafe_allow_html=True)

            # Allow downloading all markdown files as a single zip
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for path in md_files:
                    zf.writestr(path.name, path.read_text(encoding="utf-8"))
            zip_buffer.seek(0)
            st.sidebar.download_button(
                label="모두 다운로드",
                data=zip_buffer,
                file_name="all_tutorials.zip",
                mime="application/zip"
            )
        else:
            st.sidebar.info("튜토리얼이 없습니다. 먼저 생성하세요.")

if __name__ == "__main__":
    main()
