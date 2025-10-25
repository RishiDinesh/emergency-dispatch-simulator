import os
import openai
import base64
from dotenv import load_dotenv
from backend._types import Message

load_dotenv()

class LLM(object):

    def __init__(self):
        self.client = openai.Client(
            api_key = os.getenv("API_KEY"),
            base_url = os.getenv("BASE_URL")
        )
        # defined here for simplicity
        self.tts_model = "higgs-audio-generation-Hackathon"
        self.asr_model = "higgs-audio-understanding-Hackathon"
        self.chat_model = "Qwen3-32B-non-thinking-Hackathon"
        self.reasoning_model = "Qwen3-32B-thinking-Hackathon"
        self.omni_model = "Qwen3-Omni-30B-A3B-Thinking-Hackathon"
    
    # def get_text_from_speech(self)
    
    def get_speech_from_text(
            self,
            instructions: str,
            text: str,
            voice: str,
            with_streaming: bool,
            response_format: str = "pcm",
            speed: float = 1.0,
            chunk_size: int = 2048
    ):
        params = {
            "model": self.tts_model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": response_format,
            "speed": speed
        }
        if not with_streaming:
            response = self.client.audio.speech.create(**params)
            yield response.content
        else:
            with self.client.audio.speech.with_streaming_response.create(**params) as response:
                for chunk in response.iter_bytes(chunk_size = chunk_size):
                    yield chunk
    
    def get_speech_from_chat_completion(
            self,
            messages: list[Message],
            stream = True
    ):
        
        response = self.client.chat.completions.create(
            messages = [m.to_dict() for m in messages],
            model = self.tts_model,
            temperature = 1.0,
            modalities=["audio"],
            audio={"format": "wav"},
            max_completion_tokens=4096,
            stream=stream
        )
        if not stream:
            yield response.choices[0].message.audio.data
        else:
            for chunk in response:
                delta = getattr(chunk.choices[0], "delta", None)
                audio = getattr(delta, "audio", None)
                if not audio:
                    continue
                yield audio["data"]

    
    def get_chat_completion(
            self,
            messages: list[Message],
            model: str,
            max_tokens: int|None = None,
            temperature: float|None = 0.0,
            response_format: dict|None = None
    ):
        params = {
            "model": model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature
        }
        if max_tokens:
            params["max_completion_tokens"] = max_tokens
        if response_format:
            params["response_format"] = response_format
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message