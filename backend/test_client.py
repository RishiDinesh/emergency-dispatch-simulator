import asyncio, os, websockets


async def main():
    uri = "ws://localhost:8000/ws/upload?codec=webm-opus"
    async with websockets.connect(uri) as ws:
        print("Connected!")
        for i in range(5):
            fake_audio = os.urandom(2048)
            await ws.send(fake_audio)
            print(f"Sent chunk {i+1}")
            await asyncio.sleep(0.25)
        await ws.close()
        print("Closed.")


asyncio.run(main())
