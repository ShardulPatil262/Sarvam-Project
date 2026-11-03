# 📜 Sarvam AI Manuscript Audio-Visual Storyteller

An AI-powered pipeline and interactive studio that transcribes and translates ancient manuscripts into narrated audio stories with synchronized, contextual background scenes using **Sarvam AI**.

---

## ✨ Features

- **Ancient Manuscript Ingestion & Analysis**:
  - Ingests text excerpts in Sanskrit, Prakrit, Old Tamil, Pali, Hindi, etc.
  - Automatically breaks manuscripts into sequential narrative scenes using `sarvam-105b-conversations`.
- **Multilingual Storytelling Translation**:
  - Translates and adapts archaic verse into natural, dramatic oral storytelling prose across **11 Indian languages** (Hindi, Tamil, Telugu, Bengali, Kannada, Marathi, Gujarati, Punjabi, Malayalam, Odia, and Indian English).
- **Expressive Narration Audio (TTS)**:
  - Synthesizes high-fidelity human speech using Sarvam's **`bulbul:v3`** model with dedicated story narrators (`roopa`, `shubh`, `priya`, `aditya`, `gokul`, `kavitha`, `soham`, etc.).
- **Synchronized Contextual Background Artwork**:
  - Automatically crafts vivid, historical/miniature oil-painting visual prompts for each scene.
  - Dynamically updates the background imagery in real time as the narration advances from scene to scene.
- **Interactive Storyboard Player & Studio**:
  - Zero-external-dependency local web studio (`server.py`) running at `http://localhost:8000`.
  - Self-contained HTML story players with embedded base64 audio and synced bilingual subtitles.

---

## 🛠️ Project Structure

```
├── storyteller_engine.py      # Core engine pipeline (segmentation, translation, TTS, image generation)
├── server.py                  # Local Web Studio server (port 8000) with interactive UI
├── run_aitareya.py            # Complete runner script for Aitareya Aranyaka manuscript
├── aitareya_story_player.html # Standalone interactive player with synced audio and visuals
├── main.py                    # Minimal Sarvam API test script
├── .env.example               # Template for environment configuration
└── .gitignore                 # Protects sensitive API keys (.env)
```

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install sarvamai httpx
```

### 2. Configure API Key
Create a `.env` file in the root directory:
```bash
SARVAM_API_KEY=your_sarvam_api_key_here
```

### 3. Launch the Interactive Studio
```bash
python server.py
```
Open **`http://localhost:8000`** in your browser to paste manuscripts, select target languages, and generate stories.

### 4. Or Run via Python Script
```bash
python run_aitareya.py
```
This generates `aitareya_story_player.html` which you can open directly in any web browser.

---

## 🛡️ License
MIT License. Built with [Sarvam AI](https://docs.sarvam.ai/).
