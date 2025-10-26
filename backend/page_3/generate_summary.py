from backend.llm import LLM
from backend._types import Message, MessageContent, InputAudio, Log

class AnalyzeCall(object):
    def __init__(self, call_logs: list[Log]):
        self.llm = LLM()
        self.call_logs = call_logs


    def generate_summary(self, overall_summary=False):
        if overall_summary:
            output_questions = "/data/summary_prompt.txt"
        else: 
            output_questions = "/data/individual_summary_prompt.txt"

            
        system_content = "You are a 911 call trainer evaluating operator performance."

        messages = [Message(role = "system", content = system_content)]
        for call_data in self.call_logs:
            messages.append(
                {
                    Message(
                        role = "user", 
                        content = [
                            MessageContent(
                                type = "input_audio",
                                input_audio = InputAudio(
                                    data = call_data.audio,
                                    format = 'wav',
                                )
                            )
                        ]
                    )
                }
            )
        
        messages.append({"role": "user", "content": output_questions})

        return self.llm.get_text_from_speech(messages = messages)