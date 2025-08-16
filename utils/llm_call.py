from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
            
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_call(prompt: str) -> str:
    """
    주어진 프롬프트로 LLM을 동기적으로 호출합니다.
    이는 메시지를 하나의 프롬프트로 연결하는 일반적인 헬퍼 함수입니다.
    """
    messages = [{"role": "user", "content": prompt}]
    chat_completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    prompt = "Hello, world!"
    print(llm_call(prompt))
