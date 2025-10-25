from dataclasses import dataclass, asdict, is_dataclass
from typing import Optional, Union, Literal
from pydantic import BaseModel

EMOTION = Literal["sad_0", "sad_1", "angry_0", "angry_1", "fear_0", "fear_1", "neutral"]

@dataclass
class InputAudio:
    data: bytes
    format: str

@dataclass
class ImageURL:
    url: str

@dataclass
class AudioURL:
    url: str

@dataclass
class MessageContent:
    type: str
    input_audio: Optional[InputAudio] = None
    image_url: Optional[ImageURL] = None
    audio_url: Optional[AudioURL] = None
    text: Optional[str] = None

    def to_dict(self):
        base = {"type": self.type}
        # Find the corresponding field for this type
        if self.type == "input_audio" and self.input_audio:
            base["input_audio"] = asdict(self.input_audio)
        elif self.type == "image_url" and self.image_url:
            base["image_url"] = asdict(self.image_url)
        elif self.type == "audio_url" and self.audio_url:
            base["audio_url"] = asdict(self.audio_url)
        elif self.type == "text" and self.text:
            base["text"] = self.text

        return base

@dataclass
class Message:
    role: str
    content: Union[str, list[MessageContent]]

    def to_dict(self):
        if isinstance(self.content, list):
            content_dict = [
                c.to_dict() if isinstance(c, MessageContent)
                else (asdict(c) if is_dataclass(c) else c)
                for c in self.content
            ]
        elif is_dataclass(self.content):
            content_dict = asdict(self.content)
        else:
            content_dict = self.content

        return {"role": self.role, "content": content_dict}

@dataclass
class UserParams:
    incident: str
    location: str
    emotion: EMOTION
    gender: str
    language: str

    def to_dict(self):
        return asdict(self)

@dataclass
class Log:
    role: str
    timestamp: float
    audio: str
    transcription: str
    emotion: EMOTION | str