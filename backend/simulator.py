import time
import json
import base64
import asyncio
import logging
from backend.llm import LLM
from backend.environment import Environment
from backend.caller import Caller
from backend._types import UserParams, Message, MessageContent, InputAudio, EMOTION, Log
from backend.utils import get_emotion_template

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
    
    def set_current_emotion(self, emotion: EMOTION):
        logger.info(f"Updating emotion from {self.current_emotion} to : {emotion}")
        self.current_emotion = emotion
        self.env_params["emotion"] = emotion
    
    def set_system_prompt(self, caller_role: str):
        with open("backend/prompts/init_simulation.txt", "r") as f:
            prompt_template = f.read()
        return prompt_template.format(role = caller_role)
    
    def _correct_json(self, messages: list[Message], completion: str, *, max_tries: int = 3) -> dict:
        msgs = list(messages)
        for _ in range(max_tries):
            msgs.extend([
                Message(role="assistant", content=completion),
                Message(role="user", content="Response does not adhere to the given JSON schema. Please output valid JSON."),
            ])
            completion = self.llm.get_chat_completion(
                model=self.llm.asr_model,
                messages=msgs,
                temperature=0.0
            ).content
            try:
                return json.loads(completion)
            except Exception:
                logger.error(f"Error in generating JSON: {completion}")
                continue
        raise ValueError("Failed to coerce valid JSON after retries")

    
    async def analyze_speech_in(self, speech_in: str) -> list[str, str]:
        with open("backend/prompts/analyze_speech_in.txt", "r") as f:
            prompt = f.read()
        logger.info("Analyzing speech input")
        def _call():
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
            ]
            completion = self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = messages
            ).content
            try:
                res = json.loads(completion)
            except Exception as e:
                res = self._correct_json(messages, completion)
            logger.info(res)
            return res
        analysis = await _to_thread(_call)
        return (
            analysis["transcription"],
            analysis["emotion_analysis"]
        )
    
    async def get_text_out(self, speech_in: str):
        messages = self.memory.copy()
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
        messages.append(Message(role = "system", content = self.system_prompt))
        logger.info("Generating text output")
        def _call():
            completion = self.llm.get_chat_completion(
                model = self.llm.asr_model,
                messages = messages,
                temperature=0.0
            ).content
            try:
                res = json.loads(completion)
            except Exception as e:
                res = self._correct_json(messages, completion)
            logger.info(res)
            return res
        res = await _to_thread(_call)        
        return (
            res["text_response"],
            res["updated_emotion"]
        )
    
    def get_speech_out(self, text_out):
        logger.info("Converting text to speech")
        messages = get_emotion_template(
            emotion = self.current_emotion,
            gender = self.gender
        )
        messages.append(Message(
            role = "user",
            content = text_out
        ))
        generator = self.llm.get_speech_from_chat_completion(messages, self.stream)
        logger.info("Yielding from TTS generator")
        for chunk in generator:
            yield chunk

    
    async def run_simulation(self):
        
        while True:
            
            payload = await self.input_queue.get()
            if payload is None:
                logger.info("Ending simulation loop")
                break
            user_msg_ts = time.time()
            speech_in = payload["data"]
            logger.info("Received speech input from user")

            (transcript_in, emotion_in) = await self.analyze_speech_in(speech_in)
            (text_out, emotion_out) = await self.get_text_out(speech_in)         
            # async with asyncio.TaskGroup() as tg:
            #     analyze_task = tg.create_task(self.analyze_speech_in(speech_in), name="analyze_speech_in")
            #     text_task = tg.create_task(self.get_text_out(speech_in), name="get_text_out")
            # (transcript_in, emotion_in) = analyze_task.result()
            # (text_out, emotion_out) = text_task.result()

            # update current emotion
            self.set_current_emotion(emotion_out)
            
            chunks = []
            for chunk in self.get_speech_out(text_out):
                await self.output_queue.put({"data": chunk})
                chunks.append(base64.b64decode(chunk))
            if len(chunks) == 1:
                speech_out = chunks[-1]
            else:
                speech_out = base64.b64encode(b''.join(chunks)).decode("utf-8")
            logger.info(f"Completed simulation for input msg: {transcript_in}")
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
                    audio = speech_out,
                    transcription = text_out,
                    emotion = emotion_out
                )
            ])
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
        return self.simulation_logs