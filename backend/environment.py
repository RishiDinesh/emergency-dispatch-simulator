import json
from backend.llm import LLM
from backend._types import UserParams, Message

class Environment(object):

    def __init__(self):
        self.llm = LLM()
        with open("backend/data/params.json", "r") as f:
            self.all_params = json.load(f)

    def get_env_params(self, user_params: UserParams):
        user_param_dict = user_params.to_dict()
        param_set = {}
        for group in self.all_params["system"].keys():
            for key, value in self.all_params["system"][group].items():
                param_set[key] = value
        with open("backend/prompts/init_environment.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.format(
            param_set = str(param_set),
            user_context = "\n".join([f"- {k}: {v}" for k, v in user_param_dict.items()])
        )
        response = self.llm.get_chat_completion(
            messages = [
                Message(
                    role = "system",
                    content = prompt
                )
            ],
            model = self.llm.reasoning_model,
            response_format= { "type": "json_object" }
        )
        env_params = json.loads(response.content)
        env_params.update(user_param_dict)
        return env_params