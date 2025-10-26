from backend.llm import LLM
from backend._types import Message, MessageContent, InputAudio, Log

class AnalyzeCall(object):
    def __init__(self, call_logs: list[Log]):
        self.llm = LLM()
        self.call_logs = call_logs


    def generate_summary(self, message_index=-1):
        if message_index == -1:
            output_questions = "/data/summary_prompt.txt"
        else: 
            output_questions = "/data/individual_summary_prompt.txt"


        system_content = "You are a 911 call trainer evaluating operator performance."

        if message_index == -1:
            message_index = len(self.call_logs) - 1

        messages = [Message(role = "system", content = system_content)]
        for i in range(message_index+1):
            messages.append(
                {
                    Message(
                        role = "user", 
                        content = [
                            MessageContent(
                                type = "input_audio",
                                input_audio = InputAudio(
                                    data = self.call_logs[i].audio,
                                    format = 'wav',
                                )
                            )
                        ]
                    )
                }
            )
        
        messages.append({"role": "user", "content": output_questions})

        return self.llm.get_text_from_speech(messages = messages)
    