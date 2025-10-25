from backend.llm import LLM
from backend._types import Message, MessageContent, InputAudio, Log

class SummaryGenerator(object):
    def __init__(self):
        self.llm = LLM()


    def generate_summary(self, call_data: list[Log], output_questions_txt_path: str):
        system_content = "You are a 911 call trainer evaluating operator performance."
        output_questions = output_questions

        messages = [Message(role = "system", content = system_content)]
        for call_data in call_data:
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
    