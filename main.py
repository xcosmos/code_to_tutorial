import logging
from pathlib import Path
import shutil
from typing import Dict, List, Any
from utils.extract_yaml import extract_yaml_block
from utils.crawl_github_files import crawl_github_files
from utils.llm_call import llm_call

# Logger setup
g_logger = logging.getLogger(__name__)

def setup_logging(log_path: Path = Path("debug.log")) -> None:
    """
    Configure file logging.
    """
    handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    g_logger.addHandler(handler)
    g_logger.setLevel(logging.DEBUG)
    
    
# 1. 깃허브에서 코드 가져오기
def fetch_github_repo(repo_url: str, token: str = None) -> Dict[str, str]:
    """
    Fetch files from a GitHub repository using crawl_github_files.

    Returns a mapping of filename to content.
    """
    g_logger.info("Fetching GitHub repo: %s", repo_url)
    result = crawl_github_files(repo_url=repo_url, token=token)
    files = result.get("files") or {}
    if not files:
        g_logger.error("No files found in repo: %s", repo_url)
        raise RuntimeError(f"No files found in {repo_url}")
    g_logger.info("Retrieved %d files", len(files))
    g_logger.debug("fetch_github_repo 최종 결과: %s", files)
    return files

# 2. 코드의 핵심 개념 추출
def extract_abstractions(
    files: Dict[str, str],
    project_name: str = "MyProject",
    language: str = "english",
    max_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract top-level abstractions from the codebase via an LLM.

    Returns a list of dicts: name, description, files (indices).
    """
    indexed_files = list(files.items())

    # Reference list
    file_listing = "\n".join(
        f"- {i} # {path}" for i, (path, _) in enumerate(indexed_files)
    )

    # Full context assembly
    context_text = "\n\n".join(
        f"--- File Index {i}: {path} ---\n{content}"
        for i, (path, content) in enumerate(indexed_files)
    )

    language_note = (
        f"\nIMPORTANT: Write everything in {language.capitalize()}."
        if language.lower() != "english"
        else ""
    )

    # Prompt with teaching order instruction
    prompt = (
        f"Project: {project_name}{language_note}\n\n"
        f"Codebase:\n{context_text}\n\n"
        "Analyze the codebase context and identify the top "
        f"{max_n} core abstractions to teach newcomers.\n\n"
        "For each abstraction, provide:\n"
        "- name (1 line)\n"
        "- description (~100 words, simple, metaphor OK)\n"
        "- file_indices (e.g., 0, 2)\n\n"
        "Reference:\n"
        f"{file_listing}\n\n"
        "Output a YAML list in teaching order:\n```yaml\n"
        "- name: Something\n"
        "  description: |\n"
        "    This is like ...\n"
        "  file_indices:\n"
        "    - 0 # main.py\n"
        "    - 2 # router.py\n"
        "# ... up to {max_n} items\n"
        "```"
    )
    g_logger.debug("LLM prompt for extract_abstractions: %s",prompt)
    llm_output = llm_call(prompt)
    g_logger.debug("LLM output for extract_abstractions: %s", llm_output)
    parsed = extract_yaml_block(llm_output)

    abstractions: List[Dict[str, Any]] = []
    for item in parsed:
        indices = {int(str(idx).split("#")[0].strip()) for idx in item.get("file_indices", [])}
        abstractions.append({
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "files": sorted(indices)
        })

    g_logger.debug("extract_abstractions 최종 결과: %s", abstractions)
    return abstractions


# 3. 핵심 개념에 대한 튜토리얼 생성
def generate_tutorials(
    abstractions: List[Dict[str, Any]],
    files: Dict[str, str],
    output_dir: Path = Path("output"),
    project_name: str = "MyProject",
    language: str = "english",
    repo_url: str = None
) -> List[str]:
    """
    Generate markdown tutorials for each abstraction via an LLM.

    Returns list of generated file paths.
    """
        # 1) Empty or recreate the folder
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # inside generate_tutorials, after output_dir setup
    # e.g. repo_url = "https://github.com/dabidstudio/python_deepresearch"
    owner_repo = "/".join(repo_url.rstrip("/").split("/")[-2:])
    blob_base = f"https://github.com/{owner_repo}/blob/main"
    
    chapter_order = list(range(len(abstractions)))
    total_chapters = len(chapter_order)

    indexed_files = list(files.items())
    tutorial_paths: List[str] = []

    for num, idx in enumerate(chapter_order, start=1):
        abstr = abstractions[idx]
        safe_name = ''.join(c if c.isalnum() else '_' for c in abstr['name']).lower()
        filename = f"{num:02d}_{safe_name}.md"
        filepath = output_dir / filename
        print(f"generating tutorial at filepath: {filepath}")

        # Build code context
        parts = []
        for i in abstr['files']:
            if 0 <= i < len(indexed_files):
                path, content = indexed_files[i]
                file_url = f"{blob_base}/{path}"
                parts.append(
                    f"--- `{path}` ([view on GitHub]({file_url})) ---\n{content}"
                )
        code_context = "\n\n".join(parts) or "No specific code provided."

        # Language note for non-English
        language_note = (
            f"Write the full chapter in **{language.capitalize()}**, except code."
            if language.lower() != "english"
            else ""
        )

        # Previous and next chapter info
        prev_info = ""
        if num > 1:
            prev = abstractions[chapter_order[num-2]]
            prev_info = (
                f"Previous Concept ({num-1}/{total_chapters}): {prev['name']} - {prev['description']}\n\n"
            )
        next_info = ""
        if num < total_chapters:
            nxt = abstractions[chapter_order[num]]
            next_info = (
                f"Next Concept ({num+1}/{total_chapters}): {nxt['name']} - {nxt['description']}\n\n"
            )

        prompt = (
            f"{language_note}\n\n"
            f"You are writing Chapter {num}/{total_chapters} of a beginner-friendly tutorial for the project: {project_name}.\n\n"
            f"{prev_info}{next_info}"
            f"Concept ({num}/{total_chapters}): {abstr['name']}\n"
            f"Description: {abstr['description']}\n\n"
            f"Code Context:\n{code_context}\n\n"
            "Instructions:\n"
            f"- Begin with `# Chapter {num}: {abstr['name']}`\n"
            "- Follow this structure: Motivation → Key Ideas → Code → Explanation → Wrap-up\n"
            "- Use simple words and analogies.\n"
            "- Break code into chunks and explain each step.\n"
            "- Output only Markdown.\n"
        )
        g_logger.debug("LLM prompt for generate_tutorials: %s", prompt)
        # Send prompt to LLM
        content = llm_call(prompt).strip()
        if not content.startswith(f"# Chapter {num}"):
            content = f"# Chapter {num}: {abstr['name']}\n\n{content}"

        # Write file
        filepath.write_text(content, encoding='utf-8')
        tutorial_paths.append(str(filepath))

    return tutorial_paths

setup_logging()

def main():
    
    # repo_url = "https://github.com/modelcontextprotocol/python-sdk"
    # project_name = "python mcp server"
    repo_url = "https://github.com/dabidstudio/python_deepresearch"
    project_name = "python deep research"

    language = "korean"

    files = fetch_github_repo(repo_url)
    abstractions = extract_abstractions(files, project_name, language, max_n=5)
    tutorials = generate_tutorials(abstractions, files, project_name=project_name, language=language, repo_url=repo_url)


if __name__ == "__main__":
    main()

