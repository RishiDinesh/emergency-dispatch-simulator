from dataclasses import dataclass

@dataclass
class CallData:
    role: str
    audio: str
    transcription: str
    emotion: str
    emotion_lvl: int
