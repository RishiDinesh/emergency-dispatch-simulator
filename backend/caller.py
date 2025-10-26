import re
from backend.llm import LLM
from backend._types import Message

THINK_RE = re.compile(r'(?is)<think\b[^>]*>.*?</think\s*>')

def _strip_think(text: str) -> str:
    cleaned = THINK_RE.sub('', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

class Caller(object):

    def __init__(self):
        self.llm = LLM()
    
    def generate_role(self, env_params: dict):
        with open("backend/prompts/init_caller.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.format(simulation = str(env_params))
        response = self.llm.get_chat_completion(
            messages = [
                Message(
                    role = "system",
                    content = prompt
                )
            ],
            model = self.llm.reasoning_model
        )
        return _strip_think(response.content)