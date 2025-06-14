#!/usr/bin/env python3
"""
Inspirational Shorts – Automated YouTube Shorts Pipeline

This script:
1. Fetches 10 inspirational quotes from ZenQuotes.
2. Reads each quote (with author) via gTTS.
3. Creates an 8-second “serenity” vertical B-roll per quote via Stable Diffusion + text overlay.
4. Uses voice-only audio.
5. Assembles a vertical 720×1280 short with the voice audio.
6. Prepends auto-generated viral hashtags to the description.
7. Uploads each as a YouTube Short (privacy=private, scheduled, not made for children) at 5 videos per day, starting today at 09:00 UTC, every 2 hours thereafter.
8. Deletes all generated files after upload.
"""

import os
import time
import datetime
import textwrap
import random
import requests
import pickle

from diffusers import StableDiffusionPipeline
import torch
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# === Configuration ===
OUTPUT_DIR          = "temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

QUOTES_API_URL      = "https://zenquotes.io/api/quotes"
TEMPLATE_THUMB      = "resources/templates/thumbnail.png"
CLIENT_SECRETS_FILE = "client_secrets.json" # Create a clients_secrets.json with creds
CHANNEL_ID          = "#################" #Put your channel ID here
SCOPES              = ["https://www.googleapis.com/auth/youtube.upload"]

# === Serenity backgrounds for Stable Diffusion ===
print("Loading Stable Diffusion pipeline…")
device = "cuda" if torch.cuda.is_available() else "cpu"
sd_pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

SERENITY_PROMPTS = [
    "tranquil lake at sunrise with misty mountains",
    "zen garden with raked sand and soft morning light",
    "forest path at dawn with gentle fog and sunbeams",
    "mountains bathed in golden hour light over a calm valley",
    "secluded waterfall surrounded by lush greenery"
]

# === 1. Fetch 10 inspirational quotes ===
def fetch_quotes(max_entries=10):
    response = requests.get(QUOTES_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return [{"quote": item.get("q", ""), "author": item.get("a", "")} for item in data[:max_entries]]

# === 2. Text-to-speech ===
def synthesize_voice(text, out_path):
    gTTS(text=text, lang="en").save(out_path)

# === 3. Generate serenity B-roll slide video ===
def generate_broll_slide(entry, out_path):
    width, height, duration = 720, 1280, 8
    prompt = random.choice(SERENITY_PROMPTS)
    bg = sd_pipe(
        prompt, width=width, height=height,
        num_inference_steps=30, guidance_scale=7.5
    ).images[0].convert("RGB")

    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    text = f"\"{entry['quote']}\" — {entry['author']}"
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width=30) or [""]

    y = 60
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font, stroke_width=2)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (width - tw)//2
        draw.text((x, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
        y += th + 12
        if y > height - 60:
            break

    frame_path = os.path.join(OUTPUT_DIR, f"serenity_{int(time.time())}.png")
    bg.save(frame_path)
    ImageClip(frame_path).set_duration(duration).write_videofile(out_path, fps=1, codec="libx264", audio=False)
    os.remove(frame_path)

# === 4. Assemble final short with voice-only audio ===
def assemble_video(voice_fp, slide_fp, out_fp):
    voice_clip = AudioFileClip(voice_fp)
    video_clip = VideoFileClip(slide_fp).set_duration(voice_clip.duration)
    video_clip.set_audio(voice_clip).write_videofile(out_fp, fps=24, codec="libx264")

# === 5. Auto-generate hashtags ===
def generate_hashtags(entry):
    base = ["Inspiration", "Motivation", "DailyQuote", "Viral", "Shorts"]
    author_tag = entry["author"].replace(" ", "")
    return ["#" + t for t in base + [author_tag]]

# === 6. Thumbnail creation ===
def create_thumbnail(title, template, out_path):
    img = Image.open(template)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 52)
    except IOError:
        font = ImageFont.load_default()

    iw, ih = img.size
    bbox = draw.textbbox((0,0), title, font=font, stroke_width=2)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x, y = (iw - tw)//2, ih - th - 50
    draw.text((x, y), title, font=font, fill="white", stroke_width=2, stroke_fill="black")
    img.save(out_path)

# === 7. YouTube OAuth helper ===
def get_authenticated_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)

# === 8. Upload function ===
def upload_video(video_fp, title, desc, tags, publish_at):
    yt = get_authenticated_service()
    body = {
        "snippet": {"channelId": CHANNEL_ID, "title": title, "description": desc, "tags": tags},
        "status": {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False}
    }
    media = MediaFileUpload(video_fp, chunksize=-1, resumable=True)
    try:
        res = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        print("Uploaded video ID:", res["id"])
    except HttpError as e:
        if e.resp.status == 403:
            print(
                "\nERROR: YouTube Data API not enabled.\n"
                "→ Enable at: https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project=YOUR_PROJECT_ID\n"
            )
            return
        raise

# === Main pipeline ===
def main():
    quotes = fetch_quotes(10)
    start = datetime.datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
    for idx, entry in enumerate(quotes):
        title = f"Inspiration: {entry['author']}"
        quote_text = f"\"{entry['quote']}\" — {entry['author']}"
        # Paths
        voice_fp = os.path.join(OUTPUT_DIR, f"voice_{idx}.mp3")
        slide_fp = os.path.join(OUTPUT_DIR, f"slide_{idx}.mp4")
        video_fp = os.path.join(OUTPUT_DIR, f"video_{idx}.mp4")
        thumb_fp = os.path.join(OUTPUT_DIR, f"thumb_{idx}.png")
        # Generate media
        synthesize_voice(quote_text, voice_fp)
        generate_broll_slide(entry, slide_fp)
        assemble_video(voice_fp, slide_fp, video_fp)
        create_thumbnail(title, TEMPLATE_THUMB, thumb_fp)
        # Schedule
        day_offset = idx // 5
        slot = idx % 5
        publish_time = (
            start + datetime.timedelta(days=day_offset, hours=slot*2)
        ).isoformat() + "Z"
        # Upload
        hashtags = generate_hashtags(entry)
        desc = quote_text + "\n\n" + " ".join(hashtags)
        tags = [h.strip("#") for h in hashtags]
        upload_video(video_fp, title, desc, tags, publish_time)
        # Clean up
        for path in [voice_fp, slide_fp, video_fp, thumb_fp]:
            try: os.remove(path)
            except OSError: pass

if __name__ == "__main__":
    main()
