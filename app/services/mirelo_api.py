import requests
import os

def add_sound_to_video(video_url: str) -> str:
    url = "https://api.mirelo.ai/sound"
    headers = {"Authorization": f"Bearer {os.getenv('MIRELO_API_KEY')}"}
    payload = {"video_url": video_url}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["video_with_sound_url"]