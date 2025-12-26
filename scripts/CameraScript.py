import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os
import time
import pytz  # Handles the specific timezone conversion

# Configuration
IMAGE_URL = f"https://panhandlewx.altervista.org/wp-content/Latest.jpg?v={int(time.time())}"
API_URL = "https://api.ambientweather.net/v1/devices?applicationKey=40b33f6a63754b5fb70a4d5fe557c64efcdd693597924c21986b47e71e1e68eb&apiKey=c5cc20bfdc0446aaaddd4543eb04c64c4852dcd72d1f4d5d8c7f207c1d21036a"
SAVE_PATH = "./docs/Latest.jpg"

def draw_text_with_outline(draw, position, text, font):
    x, y = position
    # Thinner outline for smaller text
    for adj in range(-1, 2):
        for bdy in range(-1, 2):
            draw.text((x + adj, y + bdy), text, font=font, fill="black")
    draw.text(position, text, font=font, fill="white")

def main() -> None:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    try:
        # 1. Fetch Temperature Data
        api_res = requests.get(API_URL, timeout=15)
        api_res.raise_for_status()
        weather_data = api_res.json()[0]['lastData']
        temp_string = f"Temp: {weather_data['tempf']}°F"

        # 2. Fetch the Image
        img_res = requests.get(IMAGE_URL, timeout=20, headers={'Cache-Control': 'no-cache'})
        img_res.raise_for_status()
        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 3. Timezone Handling
        local_tz = pytz.timezone("America/Chicago")
        local_time = datetime.now(pytz.utc).astimezone(local_tz)
        timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")

        # 4. Font Setup (Smaller size)
        # Using 20pt for a cleaner, less intrusive look
        font_size = 20
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if not font:
            font = ImageFont.load_default()

        # 5. Overlay Text
        width, height = img.size
        
        # Top Left: Processed Timestamp
        draw_text_with_outline(draw, (15, 15), f"Processed: {timestamp}", font)
        
        # Bottom Left: Temperature
        draw_text_with_outline(draw, (15, height - 35), temp_string, font)

        # 6. Save
        img.save(SAVE_PATH, "JPEG", quality=95)
        print(f"Update Successful: {timestamp} (Central) | {temp_string}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
