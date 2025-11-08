from fastapi import FastAPI, File, UploadFile
from app.services.pipeline import process_image_to_sound_video
import tempfile

app = FastAPI()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        image_path = tmp.name

    final_video_url = process_image_to_sound_video(image_path)
    return {"final_video_url": final_video_url}