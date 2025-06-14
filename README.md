# 📽️ Inspirational Shorts – Automated YouTube Shorts Creator

This Python script automates the generation and scheduled uploading of inspirational YouTube Shorts using quotes, AI-generated video, and text-to-speech narration.

---

## 🔥 What It Does

1. **Fetches 10 Inspirational Quotes**  
   Pulls from the ZenQuotes API.

2. **Generates Voiceovers**  
   Converts each quote to voice using `gTTS`.

3. **Creates Vertical B-Roll Slides**  
   Uses Stable Diffusion (`runwayml/stable-diffusion-v1-5`) to generate peaceful backgrounds for each quote.

4. **Combines Audio + Video**  
   Merges the TTS audio and generated video into a vertical 720x1280 YouTube Short.

5. **Auto-generates Hashtags & Thumbnails**  
   Builds thumbnails from a template and appends viral tags based on quote content.

6. **Schedules Uploads to YouTube**  
   - Sets videos as `private`
   - Publishes 5 per day starting at **09:00 UTC**, every **2 hours**
   - Flags them as **not made for children**

7. **Deletes Generated Media After Upload**

---

## 🧰 Requirements

- Python 3.8+
- GPU (for Stable Diffusion) or fallback to CPU (slower)

### Python Libraries

Install via pip:

```bash
pip install torch diffusers gtts pillow moviepy google-auth-oauthlib google-api-python-client
```

---

## 📂 Project Structure

```
.
├── script.py
├── client_secrets.json       # Your YouTube OAuth credentials
├── token.pickle              # Auto-generated OAuth token after first run
├── resources/
│   └── templates/
│       └── thumbnail.png     # Base thumbnail template
└── temp/                     # Temp folder for generated media (auto-created)
```

---

## 🔧 Configuration

Edit the following constants at the top of the script:

```python
CHANNEL_ID = "YOUR_YOUTUBE_CHANNEL_ID"
CLIENT_SECRETS_FILE = "client_secrets.json"
TEMPLATE_THUMB = "resources/templates/thumbnail.png"
```

---

## 🚀 Usage

```bash
python script.py
```

After authenticating with your YouTube account on first run, the script will:

- Generate and voice 10 quotes
- Upload 5 videos per day (spaced 2 hours apart)
- Clean up all media files

---

## 💡 Tips

- To customize image styles, modify `SERENITY_PROMPTS`.
- To change schedule frequency or time, adjust the `start` time and `slot` logic in `main()`.

---

## ⚠️ Disclaimer

- **ZenQuotes.io** usage is subject to their terms and rate limits.
- Make sure the **YouTube Data API v3** is enabled in your Google Cloud Console.
- Do not exceed YouTube’s daily upload quota to avoid rate limits.

---

## 🙏 Credits

- Quotes: [ZenQuotes API](https://zenquotes.io/)
- Voice: [gTTS](https://pypi.org/project/gTTS/)
- AI Video: [Stable Diffusion (HuggingFace)](https://huggingface.co/runwayml/stable-diffusion-v1-5)
- YouTube Upload: [Google API Python Client](https://github.com/googleapis/google-api-python-client)

---

## 📬 Contact

For improvements, collaborations, or support, feel free to reach out.

---

