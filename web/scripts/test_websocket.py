from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import base64

app = FastAPI()

with open('./test-2mb.wav', 'rb') as infile:
    bin_file_data = infile.read()
    b64Str2Mb = base64.b64encode(bin_file_data).decode('utf-8')



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(f'received: {data}')
        await websocket.send_text(b64Str2Mb)
