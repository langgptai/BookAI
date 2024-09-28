import os
import re
import json
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import openai
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat

# 加载 .env 文件
load_dotenv()

def read_prompt(prompt_file: str, replacements: Dict[str, str]) -> str:
    """
    读取提示文件并替换占位符
    """
    with open(prompt_file, 'r', encoding='utf-8') as file:
        prompt = file.read()
    for key, value in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt

class PuyuAPIClient:
    """处理与AI API的所有交互。"""

    def __init__(self, api_key, base_url, model_name):
        """初始化APIClient。"""
        api_key = os.getenv("PUYU_API_KEY")
        base_url = os.getenv("PUYU_BASE_URL")
        model_name = os.getenv("PUYU_MODEL_NAME")
        self.api_key = api_key
        self.api_url = base_url
        self.model_name = model_name

    def call_api(self, messages: List[Dict[str, str]], max_tokens: int = 4096) -> str:
        """调用AI API并返回生成的文本。

        Args:
            messages: 要发送给API的消息列表。
            max_tokens: 响应中的最大标记数。

        Returns:
            API返回的生成文本。

        Raises:
            requests.RequestException: 如果API调用失败。
        """
        client = openai.OpenAI(api_key=self.api_key, base_url=self.api_url)

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.7,
                frequency_penalty=0.5,
                n=1
            )

            for choice in response.choices:
                return choice.message.content.strip()

        except openai.OpenAIError as e:
            print(f"API调用失败: {e}")
            raise

def convert_latex_to_markdown(text):
    # 使用正则表达式替换公式开始和结束的 \[ 和 \]，但不替换公式内部的
    pattern = r'(?<!\\)\\\[((?:\\.|[^\\\]])*?)(?<!\\)\\\]'
    return re.sub(pattern, r'$$\1$$', text)


class BookWriter:
    """管理书籍生成过程的主类。"""

    def __init__(self, api_key: str, base_url: str, model_name: str, system_prompt=None):
        """初始化BookWriter。"""
        # 使用openai的接口调用书生浦语模型

        self.api_key = os.getenv("API_KEY") if api_key is None else api_key
        self.base_url = os.getenv("BASE_URL") if base_url is None else base_url
        self.model_name = os.getenv("MODEL_NAME") if model_name is None else model_name

        if system_prompt is None:
            system_prompt = "你是一个专业的写作助手，正在帮助用户写一本书。"
        self.assistant = self.create_assistant(self.model_name, self.api_key, self.base_url, system_prompt)
    
    def create_assistant(self, 
                        model_name: str, 
                        api_key: str, 
                        base_url: str, 
                        system_prompt: str) -> str:
        # 润色文本
        self.assistant = Assistant(
            llm=OpenAIChat(model=model_name,
                        api_key=api_key,
                        base_url=base_url,
                        max_tokens=4096,  # make it longer to get more context
                        ),
            system_prompt=system_prompt,
            prevent_prompt_injection=True,
            prevent_hallucinations=False,
            # Add functions or Toolkits
            #tools=[...],
            # Show tool calls in LLM response.
            # show_tool_calls=True
        )
        return self.assistant

    def generate_title_and_intro(self, book_theme, prompt_file = "prompts/title_writer.txt") -> Tuple[str, str]:
        """生成书籍标题和主要内容介绍。

        Args:
            prompt: 用于生成标题和介绍的提示。

        Returns:
            包含生成的标题和介绍的元组。
        """
        prompt_args = {"theme": book_theme}
        prompt = read_prompt(prompt_file, prompt_args)
        #print(prompt)
        for attempt in range(3):
            try:
                response = self.assistant.run(prompt, stream=False)
                # convert to json
                response = response.strip()
                if not response.startswith('{'):
                    response = '{' + response.split('{', 1)[1]
                if not response.endswith('}'):
                    response = response.split('}', 1)[0] + '}'

                book_title_and_intro = json.loads(response)

                #print(book_title_and_intro)

                return book_title_and_intro
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
        return response

    def generate_outline(self, book_theme, book_title_and_intro: str, prompt_file= "prompts/outline_writer.txt") -> List[str]:
        """生成书籍章节大纲。

        Args:
            prompt: 用于生成大纲的提示。
            title: 书籍标题。
            intro: 书籍介绍。

        Returns:
            章节标题列表。
        """
        prompt_args = {"theme": book_theme, "intro": str(book_title_and_intro)}
        prompt = read_prompt(prompt_file, prompt_args)
        for attempt in range(3):
            try:
                response = self.assistant.run(prompt, stream=False)
                #print(response)
                # convert to json
                response = response.strip()
                if not response.startswith('['):
                    response = '[' + response.split('[', 1)[1]
                if not response.endswith(']'):
                    response = response.split(']', 1)[0] + ']'
                chapters = json.loads(response.strip())
                #print(chapters)
                return chapters
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
        return response

    def generate_chapter(self, book_content, chapter_intro, prompt_file= "prompts/chapter_writer.txt") -> str:
        """生成单个章节的内容。

        Args:
            chapter_title: 章节标题。
            book_title: 书籍标题。
            book_intro: 书籍介绍。
            outline: 完整的章节大纲。
            prompt: 用于生成章节的提示。

        Returns:
            生成的章节内容。
        """
        
        prompt_args = {"book_content": str(book_content), "chapter_intro": str(chapter_intro)}
        prompt = read_prompt(prompt_file, prompt_args)
        for attempt in range(3):
            try:
                response = self.assistant.run(prompt, stream=False)
                response.strip()
                if response.startswith('```markdown'):
                    # 删除第一行和最后一行
                    lines = response.splitlines()
                    response = '\n'.join(lines[1:-1])

                return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
        response = convert_latex_to_markdown(response)
        return response

    def generate_book(self, custom_theme=None, save_file=False) -> None:
        """生成整本书并将其保存到文件中。

        Args:
            custom_prompts: 自定义提示的字典。可以包括 'title_intro', 'outline' 和 'chapter' 键。
        """

        print("开始生成书籍标题和介绍...")
        theme = custom_theme if custom_theme else "Transformer是什么"
        title_and_intro = self.generate_title_and_intro(theme)
        title = title_and_intro["title"]
        print(f"书籍标题和介绍:\n {title_and_intro}")

        print("\n开始生成章节大纲...")
        chapters = self.generate_outline(theme, title_and_intro)
        print("章节大纲:")
        print(chapters)

        book_intro = title_and_intro
        book_content = "# " + title

        # 使用线程池来并行生成章节内容
        print("\n开始创作正文内容，时间较长（约几分钟）请等待~")
        with ThreadPoolExecutor() as executor:
            chapter_contents = list(executor.map(self.generate_chapter, [book_intro]*len(chapters), chapters))

        for i, chapter in enumerate(chapters, 1):
            print(f"\n正在生成第{i}章：{chapter}")
            chapter_content = chapter_contents[i-1].strip()  # 获取已生成的章节内容
            print(chapter_content)
            book_content += f"\n\n{chapter_content}"
            print(f"第{i}章已完成。")

        print("\n整本书已生成完毕。")
        if save_file:
            filename = f"books/{title.replace(' ', '_')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(book_content)
            
            print(f"书籍内容已保存到 {filename} 文件中。")
        return book_content

def main():
    """主函数, 演示如何使用BookWriter类。"""
    book_theme = input("请输入书籍主题(如 AI 是什么？): ")

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    print(base_url, model_name)
    book_writer = BookWriter(api_key, base_url, model_name, system_prompt=None)
    book_writer.generate_book(custom_theme=book_theme, save_file=True)

if __name__ == "__main__":
    main()