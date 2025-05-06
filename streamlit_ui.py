import streamlit as st
from pathlib import Path
import io
import zipfile

# Import your core functions
from main import fetch_github_repo, extract_abstractions, generate_tutorials

# Constants
DOCS_DIR = Path("streamlit_docs")

def run_generation(repo_url, token, project_name, language, max_n):
    try:
        files = fetch_github_repo(repo_url, token or None)
        abstractions = extract_abstractions(files, project_name, language, max_n)
        generate_tutorials(
            abstractions,
            files,
            output_dir=DOCS_DIR,
            project_name=project_name,
            language=language
        )
    except Exception as e:
        st.error(f"생성 중 오류 발생: {e}")


def main():
    st.set_page_config(page_title="📘 AI 튜토리얼 생성기", layout="wide")

    with st.sidebar.form(key="config_form"):
        st.title("📘 AI 튜토리얼 생성기")
        repo_url      = st.text_input("GitHub 저장소 URL", value="https://github.com/dabidstudio/python_deepresearch")
        token         = st.text_input("GitHub 토큰 (선택)", type="password")
        project_name  = st.text_input("프로젝트 이름", value="My Project")
        language      = st.selectbox("언어", options=["korean", "english"], index=0)
        max_n         = st.number_input("챕터 수", min_value=1, max_value=10, value=6)
        generate_btn  = st.form_submit_button("튜토리얼 생성")

    if generate_btn:
        run_generation(repo_url, token, project_name, language, max_n)

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
