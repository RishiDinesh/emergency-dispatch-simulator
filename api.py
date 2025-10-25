# api.py
import os
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect, Query

from backend.simulator import Simulator
from backend.session import Session
from backend._types import UserParams

app = FastAPI()

AUDIO_SAVE_DIR = Path(os.getenv("AUDIO_SAVE_DIR", "./recordings"))
AUDIO_SAVE_DIR.mkdir(parents=True, exist_ok=True)

input_queue: asyncio.Queue = asyncio.Queue()
output_queue: asyncio.Queue = asyncio.Queue()

simulator_task: Optional[asyncio.Task] = None
current_user_params: Optional[UserParams] = None



@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.post("/submit_form")
async def submit_form(
    incident: str = Form(...),
    location: str = Form(...),
    emotion: str = Form(...),
    gender: str = Form(...),
    language: str = Form(...),
):
    
    global simulator_task, current_user_params

    current_user_params = UserParams(
        incident=incident,
        location=location,
        emotion=emotion,
        gender=gender,
        language=language,
    )

    Session.set(input_queue=input_queue, output_queue=output_queue)

    if simulator_task and not simulator_task.done():
        simulator_task.cancel()
        try:
            await asyncio.sleep(0)
        except Exception:
            pass

    sim = Simulator(user_params=current_user_params, stream=True)
    simulator_task = asyncio.create_task(sim.run_simulation())

    return {
        "message": "Simulator started successfully.",
        "params": current_user_params.__dict__,
    }




@app.websocket("/ws/upload")
async def ws_upload(
    ws: WebSocket,
    codec: Optional[str] = Query(None, description="e.g., wav, webm-opus, ogg"),
):
    await ws.accept()

    if current_user_params is None or simulator_task is None or simulator_task.done():
        await ws.send_text("Simulator not initialized. Submit form first.")
        await ws.close(code=1011)
        return

    # Optional debug copy
    ext = "wav" if (codec and "wav" in codec.lower()) else "raw"
    dbg_path = AUDIO_SAVE_DIR / f"{datetime.utcnow():%Y%m%d-%H%M%S}-upload.{ext}"
    f = dbg_path.open("ab", buffering=0)

    buf = bytearray()
    try:
        while True:
            msg = await ws.receive()

            if msg["type"] == "websocket.disconnect":
                break

            if msg["type"] == "websocket.receive":
                if (b := msg.get("bytes")) is not None:
                    buf.extend(b)
                    f.write(b)
                elif (t := msg.get("text")) is not None:
                    if t.strip().lower() == "stop":
                        break

        if buf:
            b64 = base64.b64encode(bytes(buf)).decode("utf-8")
            await input_queue.put({"data": b64})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[UPLOAD] error: {e!r}")
        try:
            await ws.close(code=1011)
        except Exception:
            pass
    finally:
        try: f.close()
        except Exception: pass
        try: await ws.close()
        except Exception: pass




@app.websocket("/ws/download")
async def ws_download(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            item = await output_queue.get() 
            if item is None:
                break
            b64 = item.get("data")
            if not b64:
                continue
            try:
                data = base64.b64decode(b64)
            except Exception:
                continue
            await ws.send_bytes(data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[DOWNLOAD] error: {e!r}")
    finally:
        try:
            await ws.close()
        except Exception:
            pass
