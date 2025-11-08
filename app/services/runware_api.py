import requests
import os

def generate_video_from_image(image_path: str) -> str:
    url = "https://api.runware.ai/video"
    headers = {"Authorization": f"Bearer {os.getenv('RUNWARE_API_KEY')}"}
    files = {"image": open(image_path, "rb")}

    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    video_url = response.json()["video_url"]
    return video_url