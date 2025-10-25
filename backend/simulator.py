import time
import json
import base64
import asyncio
from backend.llm import LLM
from backend.session import Session
from backend.environment import Environment
from backend.caller import Caller
from backend._types import UserParams, Message, MessageContent, InputAudio, SpeechInAnalysis, TextResponse, EMOTION, Log
from backend.utils import get_emotion_template

async def _to_thread(fn, *a, **kw):
    return await asyncio.to_thread(fn, *a, **kw)

class Simulator(object):

    def __init__(self, user_params: UserParams, stream: bool = True):
        self.llm = LLM()
        caller = Caller()
        env = Environment()
        self.env_params = env.get_env_params(user_params)
        self.caller_role = caller.generate_role(self.env_params)
        self.system_prompt = self.set_system_prompt(self.caller_role)
        self.emotion_template = get_emotion_template(
            emotion = user_params.emotion,
            gender = user_params.gender
        )
        self.memory = []
        self.stream = stream
        self.current_emotion: EMOTION = user_params.emotion
        self.gender = user_params.gender
        self.simulation_logs = []
    
    def set_current_emotion(self, emotion: EMOTION):
        self.current_emotion = emotion
        self.env_params["emotion"] = emotion
    
    def set_system_prompt(self, caller_role: str):
        with open("backend/prompts/init_simulation.txt", "r") as f:
            prompt_template = f.read()
        return prompt_template.format(role = caller_role)
    
    async def analyze_speech_in(self, speech_in: str) -> list[str, str]:
        with open("backend/prompts/analyze_speech_in.txt", "r") as f:
            prompt = f.read()
        print("analzying speech in")
        def _call():
            return json.loads(self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = [
                    Message(role = "system", content = prompt),
                    Message(
                        role = "user",
                        content = [
                            MessageContent(
                                type = "input_audio",
                                input_audio = InputAudio(
                                    data = speech_in,
                                    format = "wav"
                                )
                            )
                        ]
                    )
                ],
                temperature = 0.0,
                response_format = { "type": "json_object" } 
            ).content)
        analysis = await _to_thread(_call)
        print(analysis)
        return (
            analysis["transcription"],
            analysis["emotion_analysis"]
        )
    
    async def get_text_out(self, speech_in: str):
        # add the system header
        messages = [Message(role = "system", content = self.system_prompt)]
        # add memory
        messages = messages + self.memory
        with open("backend/prompts/generate_response.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.format(current_emotion = self.current_emotion)
        # add response instructions and input speech
        messages.extend([
            Message(
                role = "system",
                content = prompt
            ),
            Message(
                role = "user",
                content = [
                    MessageContent(
                        type = "input_audio",
                        input_audio = InputAudio(
                            data = speech_in,
                            format = "wav"
                        )
                    )
                ]
            )
        ])
        print("generating text out")
        def _call():
            return json.loads(self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = messages,
                temperature = 0.0,
                response_format= { "type": "json_object" }
            ).content)
        res = await _to_thread(_call)
        print(res)
        return (
            res["text_response"],
            res["updated_emotion"]
        )
    
    def get_speech_out(self, text_out):
        messages = get_emotion_template(
            emotion = self.current_emotion,
            gender = self.gender
        )
        messages.append(Message(
            role = "user",
            content = text_out
        ))
        generator = self.llm.get_speech_from_chat_completion(messages, self.stream)
        yield from generator

    
    async def run_simulation(self):
        input_queue: asyncio.Queue = Session.get("input_queue")
        output_queue: asyncio.Queue = Session.get("output_queue")
        while True:
            
            payload = await input_queue.get()
            if payload is None:
                break
            print("running sim step")
            user_msg_ts = time.time()
            speech_in = payload["data"]
            transcript_in, emotion_in = await self.analyze_speech_in(speech_in)
            text_out, emotion_out = await self.get_text_out(speech_in)
            # async with asyncio.TaskGroup() as tg:
            #     analyze_task = tg.create_task(self.analyze_speech_in(speech_in), name="analyze_speech_in")
            #     text_task = tg.create_task(self.get_text_out(speech_in),     name="get_text_out")
            # (transcript_in, emotion_in) = analyze_task.result()
            # (text_out, emotion_out) = text_task.result()

            # update current emotion
            self.set_current_emotion(emotion_out)
            
            chunks = []
            for chunk in self.get_speech_out(text_out):
                await output_queue.put({"data": chunk})
                chunks.append(base64.b64decode(chunk))
            self.simulation_logs.extend([
                Log(
                    role = "user",
                    timestamp = user_msg_ts,
                    audio = speech_in,
                    transcription = transcript_in,
                    emotion = emotion_in
                ),
                Log(
                    role = "assistant",
                    timestamp = time.time(),
                    audio = base64.b64encode(b''.join(chunks)).decode("utf-8"),
                    transcription = text_out,
                    emotion = emotion_out
                )
            ])



