import json
import requests
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend._types import Message, MessageContent, InputAudio

def get_emotion_template(emotion: str, gender: str):
    
    with open("backend/data/emotion_templates.json", "r") as f:
        templates = json.load(f)

    items = templates[emotion][gender]
    urls = [item["url"] for item in items]
    transcripts = [item["transcript"] for item in items]

    def fetch_b64(url: str) -> str:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("utf-8")

    # Fetch in parallel
    encoded = [None] * len(urls)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_to_idx = {pool.submit(fetch_b64, url): i for i, url in enumerate(urls)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            try:
                encoded[i] = fut.result()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch {urls[i]}: {e}") from e

    # Build messages
    messages = []
    for transcript, b64 in zip(transcripts, encoded):
        messages.append([
            Message(role="user", content=transcript),
            Message(
                role="assistant",
                content=[MessageContent(
                    type="input_audio",
                    input_audio=InputAudio(data=b64, format="wav")
                )]
            )
        ])
    return messages
