from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import base64

app = FastAPI()

with open('./test-2mb.wav', 'rb') as infile:
    bin_file_data = infile.read()
    bytes2Mb = bin_file_data


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # print(f'received: {data}')
        await websocket.send_bytes(bytes2Mb)
