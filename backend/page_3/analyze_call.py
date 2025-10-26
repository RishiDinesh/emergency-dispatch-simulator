from backend.llm import LLM
from backend._types import Message, MessageContent, InputAudio, Log

class AnalyzeCall(object):
    def __init__(self, call_logs: list[Log]):
        self.llm = LLM()
        self.call_logs = call_logs


    def generate_summary(self, message_index=-1):
        if message_index == -1:
            output_questions = "/backend/data/summary_prompt.txt"
        else: 
            output_questions = "/backend/data/individual_summary_prompt.txt"

        system_content = "You are a 911 call trainer evaluating operator performance. Here is a conversation."

        guidelines = "/backend/data/operator_evaluation_guidelines.txt"

        followup_questions = "Organize your feedback into three bulletpoints for things I did well and three bulletpoints for things I did poorly. Focus on how I said what I said as well as what I said. Don't be too verbose."

        if message_index == -1:
            message_index = len(self.call_logs) - 1

        messages = [Message(role = "system", content = system_content)]
        for i in range(message_index+1):
            messages.append(
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
            )
        
        messages.append(Message(role = "user", content = output_questions))
        if message_index == len(self.call_logs)-1:
            messages.append(Message(role = "user", content = followup_questions))
            messages.append(Message(role = "user", content = guidelines))

        return self.llm.get_text_from_speech(messages = messages)
    