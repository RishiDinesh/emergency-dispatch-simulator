import time
import json
import asyncio
import logging
import base64
from pathlib import Path
from backend.llm import LLM
from backend.environment import Environment
from backend.caller import Caller
from backend._types import UserParams, Message, MessageContent, InputAudio, EMOTION, Log
from backend.utils import get_emotion_template, memory_to_string

logger = logging.getLogger(__name__)

async def _to_thread(fn, *a, **kw):
    return await asyncio.to_thread(fn, *a, **kw)

class Simulator(object):

    def __init__(self,
        user_params: UserParams,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        stream: bool = False
    ):
        self.llm = LLM()
        caller = Caller()
        env = Environment()
        logger.info("Initializing simulator")
        self.env_params = env.get_env_params(user_params)
        logger.info(f"Initialized environment with params:\n{json.dumps(self.env_params, indent=2)}")
        self.caller_role = caller.generate_role(self.env_params)
        logger.info(f"Initialized caller with role: {self.caller_role}")
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
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.save_recordings = True
    
    def set_system_prompt(self, caller_role: str):
        with open("backend/prompts/init_simulation.txt", "r") as f:
            prompt_template = f.read()
        return prompt_template.format(role = caller_role)
    
    async def transcribe_speech_in(self, speech_in: str) -> str:
        prompt = "Transcribe the given user audio. Output only the transcription."
        logger.info("Transcribing speech input")
        def _call():
            messages = [
                Message(role = "system", content = prompt),
                Message(role = "user", content = [MessageContent(type = "input_audio", input_audio = InputAudio(data = speech_in, format = "wav"))])
            ]
            completion = self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = messages
            ).content
            return completion
        transcription = await _to_thread(_call)
        logger.info(f"Transcription: {transcription}")
        return transcription
    
    async def get_text_out(self, speech_in: str):
        memory_str = memory_to_string(self.memory.copy())
        prompt = self.system_prompt + f"\n\n#CONVERSATION HISTORY:\n{memory_str}"
        with open("backend/prompts/generate_response.txt", "r") as f:
            resp_instructions = f.read()
        resp_instructions = resp_instructions.format(current_emotion = self.current_emotion)
        prompt = prompt + f"\n\n{resp_instructions}"
        with open("prompt.txt", "w") as f:
            f.write(prompt)
        
        messages = [
            Message(role = "system", content = prompt),
            Message(role = "user", content = [MessageContent(type = "input_audio", input_audio = InputAudio(data = speech_in, format = "wav"))])
        ]
        
        logger.info("Generating text output")
        def _call():
            completion = self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = messages,
                temperature=0.0
            ).content
            return completion
        res = await _to_thread(_call)
        logger.info(res)
        return res

    def get_speech_out(self, text_out):
        messages = get_emotion_template(
            emotion = self.current_emotion,
            gender = self.gender
        )
        messages.append(Message(
            role = "user",
            content = f"[SPEAKER] {text_out}"
        ))
        generator = self.llm.get_speech_from_chat_completion(messages, self.stream)
        data = next(generator)
        return data
    
    async def run_simulation(self, load_from_recordings = False):
        counter = 0
        while True:
            payload = await self.input_queue.get()
            if payload is None:
                logger.info("Ending simulation loop")
                break
            counter += 1
            user_msg_ts = time.time()
            speech_in = payload["data"]
            logger.info("Received speech input from user")

            transcript_in = await self.transcribe_speech_in(speech_in)
            text_out = await self.get_text_out(speech_in)
            if load_from_recordings:
                with open(f"backend/recordings/audio_{counter}.wav", "rb") as f:
                    speech_out = base64.b64encode(f.read()).decode("utf-8")
                    time.sleep(3)
            else:
                speech_out = self.get_speech_out(text_out)
            await self.output_queue.put({"data": speech_out})
            logger.info(f"Completed simulation for input msg: {transcript_in}")
            logs = [
                Log(
                    role = "user",
                    timestamp = user_msg_ts,
                    audio = speech_in,
                    transcription = transcript_in
                ),
                Log(
                    role = "assistant",
                    timestamp = time.time(),
                    audio = speech_out,
                    transcription = text_out
                )
            ]
            self.simulation_logs.extend(logs)
            self.memory.extend([
                Message(
                    role = "user",
                    content = transcript_in
                ),
                Message(
                    role = "assistant",
                    content = text_out
                )
            ])
            if self.save_recordings:
                audio_bytes = base64.b64decode(logs[1].audio, validate=True)
                out_path = Path(f"backend/recordings/audio_{counter}.wav")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(audio_bytes)
        return self.simulation_logs