from .runware_api import generate_video_from_image
from .mirelo_api import add_sound_to_video

def process_image_to_sound_video(image_path: str) -> str:
    # Step 1: Generate video from image
    video_url = generate_video_from_image(image_path)

    # Step 2: Add sound using Mirelo
    final_video_url = add_sound_to_video(video_url)

    return final_video_url