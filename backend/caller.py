from backend.llm import LLM
from backend._types import Message

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
            model = self.llm.chat_model
        )
        return response.content