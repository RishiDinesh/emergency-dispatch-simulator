import base64
import asyncio
from backend.simulator import Simulator
from backend._types import UserParams
import logging
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
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()
    simulator = Simulator(
        input_queue=input_queue,
        output_queue=output_queue,
        user_params = UserParams(
            incident = "house fire",
            location = "house",
            emotion = "fear_1",
            gender = "male",
            language = "english"
        )
    )

    asyncio.create_task(simulator.run_simulation())
    user_messages_list = [
        "usermsg1.wav",
        "usermsg2.wav",
        "usermsg3.wav"
    ]
    for i, msg in enumerate(user_messages_list):
        user_msg = file_to_base64(msg)
        await input_queue.put({"data": user_msg})
        item = await output_queue.get()
        response = item["data"]
        base64_to_file(response, f"ass_msg_{i}.wav")

if __name__ == "__main__":
    asyncio.run(main())