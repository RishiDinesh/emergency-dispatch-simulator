import base64
import asyncio
from backend.simulator import Simulator
from backend._types import UserParams, Log
import logging

from backend.page_3.analyze_call import AnalyzeCall

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def file_to_base64(filename: str) -> str:
    with open(filename, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

def base64_to_file(b64_str: str, output_filename: str):
    data = base64.b64decode(b64_str)
    with open(output_filename, "wb") as f:
        f.write(data)

import logging
logger = logging.getLogger(__name__)
async def main():
    logger.info("hello")
    # input_queue = asyncio.Queue()
    # output_queue = asyncio.Queue()
    # simulator = Simulator(
    #     input_queue=input_queue,
    #     output_queue=output_queue,
    #     user_params = UserParams(
    #         incident = "sexual_assault",
    #         location = "transit",
    #         emotion = "angry_1",
    #         gender = "female",
    #         language = "english"
    #     )
    # )

    # asyncio.create_task(simulator.run_simulation())
    # user_messages_list = [
    #     "bad_assistant_1.wav",
    #     "bad_assistant_2.wav",
    #     "bad_assistant_3.wav"
    # ]

    

    # for i, msg in enumerate(user_messages_list):
    #     user_msg = file_to_base64(msg)
    #     await input_queue.put({"data": user_msg})
    #     item = await output_queue.get()
    #     response = item["data"]
    #     base64_to_file(response, f"ass_msg_assault_{i}.wav")
    

    caller_messages = []
    
    for i in range(0,3):
        with open(f"ass_msg_assault_{i}.wav", "rb") as audio_file:
            b64 = base64.b64encode(audio_file.read()).decode("utf-8")
            log = Log(role='user',timestamp=0,audio=b64,transcription="",emotion="")
            caller_messages.append(log)

    assistant_messages = []
    
    for i in range(1,4):
        with open(f"bad_assistant_{i}.wav", "rb") as audio_file:
            b64 = base64.b64encode(audio_file.read()).decode("utf-8")
            log = Log(role='assistant',timestamp=0,audio=b64,transcription="",emotion="")
            assistant_messages.append(log)
        

    combined_messages = [item for pair in zip(assistant_messages, caller_messages) for item in pair]

    analyzer = AnalyzeCall(combined_messages)

    summary = analyzer.generate_summary(message_index=0)

    logger.info("TEST " + summary)



if __name__ == "__main__":
    asyncio.run(main())