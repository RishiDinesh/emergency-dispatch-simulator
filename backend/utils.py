import json
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend._types import Message, MessageContent, InputAudio

def get_emotion_template(emotion: str, gender: str):
    
    with open("backend/data/emotion_templates.json", "r") as f:
        templates = json.load(f)

    items = templates[emotion][gender]
    filenames = [item["file_name"] for item in items]
    transcripts = [item["transcript"] for item in items]

    def load_b64(filename: str) -> str:
        path = f"backend/data/emotion_template_files/{filename}.wav"
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")

    # Fetch in parallel
    encoded = [None] * len(filenames)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_to_idx = {pool.submit(load_b64, fname): i for i, fname in enumerate(filenames)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            try:
                encoded[i] = fut.result()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch {filenames[i]}: {e}") from e

    # Build messages
    messages = []
    for transcript, b64 in zip(transcripts, encoded):
        messages.extend([
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
