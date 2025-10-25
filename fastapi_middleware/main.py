import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect, Query, HTTPException


app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.post("/submit_form")
async def submit_form(
    age: int = Form(...), gender: str = Form(...), scenario: str = Form(...)
):

    # For now, just echo back the data (you can add logic here)
    return {
        "message": "Form received successfully",
        "data": {"age": age, "gender": gender, "scenario": scenario},
    }


AUDIO_SAVE_DIR = os.getenv("AUDIO_SAVE_DIR", "./recordings")
os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)


@app.websocket("/ws/upload")
async def ws_upload(
    ws: WebSocket,
    codec: Optional[str] = Query(
        None, description="Optional hint: e.g., webm-opus, pcm16le, wav, ogg"
    ),
):

    await ws.accept()

    ext = "webm"
    if codec:
        cl = codec.lower()
        if "wav" in cl:
            ext = "wav"
        elif "pcm" in cl:
            ext = "pcm"
        elif "ogg" in cl:
            ext = "ogg"
        elif "mp3" in cl:
            ext = "mp3"

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(AUDIO_SAVE_DIR, f"{timestamp}-recording.{ext}")

    # Open file in append mode (write chunks continuously)
    f = open(out_path, "ab", buffering=0)

    chunk_count = 0
    total_bytes = 0

    try:
        while True:
            msg = await ws.receive()

            if msg["type"] == "websocket.disconnect":
                break

            if msg["type"] == "websocket.receive" and msg.get("bytes"):
                data: bytes = msg["bytes"]
                f.write(data)
                chunk_count += 1
                total_bytes += len(data)

            # (Optional) Handle text messages if you send control commands
            elif msg["type"] == "websocket.receive" and msg.get("text"):
                # Example: if you wanted to handle {"cmd": "stop"}
                pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e!r}")
        try:
            await ws.close(code=1011)
        except Exception:
            pass
    finally:
        f.close()
        print(
            f"[INFO] Closed connection: chunks={chunk_count}, bytes={total_bytes}, file={out_path}"
        )


THIRD_PARTY_URL = "ws://localhost:9000/playback"


@app.websocket("/ws/download")
async def ws_download(ws: WebSocket):
    """Single browser connects here; we forward bytes from the third-party WS."""
    await ws.accept()

    try:
        async with websockets.connect(THIRD_PARTY_URL) as upstream:
            while True:
                msg = await upstream.recv()
                if msg is None:
                    break
                if isinstance(msg, (bytes, bytearray)):
                    await ws.send_bytes(msg)
    except Exception:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
