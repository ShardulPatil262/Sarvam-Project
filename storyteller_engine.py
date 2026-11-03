import os
import re
import json
import base64
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from sarvamai import SarvamAI

# Load .env variables
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

# Language display names and default Bulbul:v3 speakers
SUPPORTED_LANGUAGES = {
    "hi-IN": {"name": "Hindi (हिंदी)", "default_speaker": "roopa", "all_speakers": ["roopa", "shubh", "priya", "aditya", "kavya"]},
    "en-IN": {"name": "English (Indian)", "default_speaker": "shubh", "all_speakers": ["shubh", "ishita", "priya", "roopa"]},
    "bn-IN": {"name": "Bengali (বাংলা)", "default_speaker": "shubh", "all_speakers": ["shubh", "roopa"]},
    "ta-IN": {"name": "Tamil (தமிழ்)", "default_speaker": "gokul", "all_speakers": ["gokul", "vijay", "shubh"]},
    "te-IN": {"name": "Telugu (తెలుగు)", "default_speaker": "kavitha", "all_speakers": ["kavitha", "tarun", "pooja"]},
    "kn-IN": {"name": "Kannada (ಕನ್ನಡ)", "default_speaker": "shubh", "all_speakers": ["shubh", "roopa"]},
    "mr-IN": {"name": "Marathi (मराठी)", "default_speaker": "soham", "all_speakers": ["soham", "rupali", "shubh"]},
    "gu-IN": {"name": "Gujarati (ગુજરાતી)", "default_speaker": "pooja", "all_speakers": ["pooja", "shubh"]},
    "pa-IN": {"name": "Punjabi (ਪੰਜਾਬੀ)", "default_speaker": "anand", "all_speakers": ["anand", "shubh"]},
    "ml-IN": {"name": "Malayalam (മലയാളം)", "default_speaker": "shubh", "all_speakers": ["shubh", "roopa"]},
    "od-IN": {"name": "Odia (ଓଡ଼ିଆ)", "default_speaker": "shubh", "all_speakers": ["shubh", "roopa"]},
}

class ManuscriptStorytellerEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY is not set.")
        self.client = SarvamAI(api_subscription_key=self.api_key)

    def analyze_and_segment(self, manuscript_text: str, target_lang: str = "hi-IN") -> Dict[str, Any]:
        """
        Uses sarvam-105b-conversations to analyze the manuscript,
        structure it into dramatic narrative scenes, and provide rich visual descriptions.
        """
        lang_info = SUPPORTED_LANGUAGES.get(target_lang, {"name": "Hindi"})
        lang_name = lang_info["name"]

        prompt = f"""You are a master storyteller and art director adapting an ancient manuscript into an immersive narrated story with accompanying visual scenes.

Analyze the following manuscript excerpt and break it down into 2 to 4 sequential narrative scenes.
For each scene, provide:
1. "scene_id": Integer (1, 2, 3...)
2. "manuscript_excerpt": The original passage corresponding to this moment.
3. "narration_text": Expressive, dramatic storytelling narration strictly in {lang_name} suitable for text-to-speech audio narration. Make it engaging, evocative, and rhythmic like an authentic oral story. Keep it under 250 characters per scene so the narration is crisp.
4. "visual_prompt": A highly detailed, atmospheric illustration prompt depicting the exact moment (style: classical Indian miniature oil painting, dramatic lighting, historic architecture, rich cinematic colors, 8k wallpaper). Do NOT include text or speech bubbles.

Return ONLY a valid JSON object with the following schema:
{{
  "story_title": "Title of the story in {lang_name}",
  "scenes": [
    {{
      "scene_id": 1,
      "manuscript_excerpt": "...",
      "narration_text": "...",
      "visual_prompt": "..."
    }}
  ]
}}

Manuscript:
\"\"\"
{manuscript_text}
\"\"\"
"""
        response = self.client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()

        # Extract JSON from potential code block
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return data
            except json.JSONDecodeError:
                pass

        # Fallback segmentation if JSON parsing fails
        paragraphs = [p.strip() for p in manuscript_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [manuscript_text.strip()]

        scenes = []
        for idx, para in enumerate(paragraphs[:4], 1):
            scenes.append({
                "scene_id": idx,
                "manuscript_excerpt": para,
                "narration_text": para,
                "visual_prompt": f"Ancient manuscript illustration of {para[:80]}, classical Indian painting style, cinematic golden lighting."
            })
        return {"story_title": "Manuscript Narration", "scenes": scenes}

    def synthesize_speech(self, text: str, lang_code: str = "hi-IN", speaker: Optional[str] = None) -> str:
        """
        Synthesizes audio using Sarvam Bulbul:v3 and returns base64 MP3.
        """
        lang_config = SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES["hi-IN"])
        chosen_speaker = speaker or lang_config["default_speaker"]

        try:
            res = self.client.text_to_speech.convert(
                text=text,
                language_code=lang_code,
                speaker=chosen_speaker,
                model="bulbul:v3",
                output_audio_codec="mp3"
            )
            if res.audios and len(res.audios) > 0:
                return res.audios[0]
        except Exception as e:
            # Fallback to general speaker if specific speaker fails
            if chosen_speaker != "shubh":
                try:
                    res = self.client.text_to_speech.convert(
                        text=text,
                        language_code=lang_code,
                        speaker="shubh",
                        model="bulbul:v3",
                        output_audio_codec="mp3"
                    )
                    if res.audios and len(res.audios) > 0:
                        return res.audios[0]
                except Exception as inner_e:
                    print(f"TTS error: {inner_e}")
            print(f"Primary TTS error: {e}")
        return ""

    def get_image_url(self, prompt: str, seed: int = 42) -> str:
        """
        Returns a high-quality contextual illustration URL for the scene prompt.
        Uses Pollinations AI free image endpoint.
        """
        styled_prompt = f"{prompt}, masterpiece, cinematic lighting, ancient historic painting, atmospheric, highly detailed"
        encoded = urllib.parse.quote_plus(styled_prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&nologo=true"

    def process_story(self, manuscript_text: str, target_lang: str = "hi-IN", speaker: Optional[str] = None) -> Dict[str, Any]:
        """
        Full end-to-end pipeline:
        1. Breaks manuscript into scenes with narrative text & visual prompts
        2. Generates TTS audio for each scene via Sarvam Bulbul:v3
        3. Attaches contextual background visuals for synchronized storytelling
        """
        data = self.analyze_and_segment(manuscript_text, target_lang)
        scenes = data.get("scenes", [])

        processed_scenes = []
        for i, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", i + 1)
            narration = scene.get("narration_text", "")
            excerpt = scene.get("manuscript_excerpt", "")
            visual_prompt = scene.get("visual_prompt", "")

            # Generate Audio
            audio_b64 = self.synthesize_speech(narration, target_lang, speaker)

            # Generate Image URL
            img_url = self.get_image_url(visual_prompt, seed=100 + scene_id * 17)

            processed_scenes.append({
                "scene_id": scene_id,
                "manuscript_excerpt": excerpt,
                "narration_text": narration,
                "visual_prompt": visual_prompt,
                "image_url": img_url,
                "audio_base64": audio_b64
            })

        return {
            "story_title": data.get("story_title", "Manuscript Narration"),
            "target_language": target_lang,
            "target_language_name": SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", target_lang),
            "scenes": processed_scenes
        }

    def generate_html_player(self, story_data: Dict[str, Any], output_path: str):
        """
        Generates a standalone, fully interactive HTML player with synchronized
        audio narration, cinematic scene transitions, and bilingual subtitles.
        """
        scenes_json = json.dumps(story_data.get("scenes", []), ensure_ascii=False)
        title = story_data.get("story_title", "Manuscript Narration")
        lang_name = story_data.get("target_language_name", "Indian Language")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Sarvam Manuscript Storyteller</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @keyframes pulse-subtle {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.02); }}
    }}
    .bg-kenburns {{
      transition: background-image 1.2s ease-in-out, transform 12s ease-out;
      background-size: cover;
      background-position: center;
    }}
  </style>
</head>
<body class="bg-stone-950 text-stone-100 min-h-screen flex flex-col font-sans selection:bg-amber-700 selection:text-white">

  <!-- Main Canvas / Dynamic Background -->
  <div id="backdrop" class="fixed inset-0 bg-kenburns z-0">
    <div class="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-950/70 to-stone-950/40"></div>
    <div class="absolute inset-0 backdrop-blur-[2px]"></div>
  </div>

  <!-- Foreground Content -->
  <div class="relative z-10 flex-1 flex flex-col max-w-5xl mx-auto w-full px-6 py-8 justify-between">
    
    <!-- Top Header -->
    <header class="flex items-center justify-between border-b border-stone-800/80 pb-4">
      <div>
        <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-900/40 text-amber-300 border border-amber-700/50">
          📜 Sarvam AI Manuscript Storyteller
        </span>
        <h1 id="storyTitle" class="text-2xl md:text-3xl font-serif font-bold text-amber-100 mt-1">{title}</h1>
        <p class="text-xs text-stone-400">Narrated in <span class="text-amber-400 font-semibold">{lang_name}</span> via Sarvam Bulbul:v3</p>
      </div>

      <!-- Scene Indicator -->
      <div class="bg-stone-900/80 backdrop-blur border border-stone-700/60 px-4 py-2 rounded-xl text-right">
        <span class="text-xs text-stone-400 block uppercase tracking-wider">Current Scene</span>
        <span id="sceneBadge" class="text-lg font-bold text-amber-400">1 / 1</span>
      </div>
    </header>

    <!-- Center Stage: Scene Artwork + Subtitles -->
    <main class="my-auto py-6 grid md:grid-cols-12 gap-8 items-center">
      
      <!-- Visual Display Card -->
      <div class="md:col-span-6 relative group">
        <div class="aspect-[4/3] rounded-2xl overflow-hidden border-2 border-amber-600/30 shadow-2xl bg-stone-900 relative">
          <img id="sceneImage" src="" alt="Scene Illustration" class="w-full h-full object-cover transition-opacity duration-700 opacity-0" onload="this.classList.remove('opacity-0')">
          <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-4">
            <p id="imagePromptText" class="text-xs text-stone-300 italic line-clamp-2"></p>
          </div>
        </div>
      </div>

      <!-- Narration & Manuscript Subtitles -->
      <div class="md:col-span-6 space-y-5">
        
        <!-- Spoken Story Narration (Large) -->
        <div class="bg-stone-900/85 backdrop-blur-md border border-stone-700/60 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div class="absolute top-0 left-0 w-1.5 h-full bg-amber-500"></div>
          <span class="text-[11px] font-semibold uppercase tracking-wider text-amber-400/90 block mb-2">Narrated Audio (Spoken Story)</span>
          <p id="narrationText" class="text-xl md:text-2xl font-serif text-amber-50 leading-relaxed min-h-[5rem]">
            Loading narration...
          </p>
        </div>

        <!-- Original Manuscript Excerpt (Accordion/Context) -->
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-4">
          <span class="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-1">Original Manuscript Excerpt</span>
          <p id="manuscriptExcerpt" class="text-sm font-mono text-stone-300 leading-normal italic">
            ...
          </p>
        </div>

      </div>
    </main>

    <!-- Bottom Audio Controls & Scene Timeline -->
    <footer class="bg-stone-900/90 backdrop-blur-lg border border-stone-800 rounded-2xl p-5 shadow-2xl space-y-4">
      
      <!-- Scene Navigation Timeline -->
      <div id="sceneTimeline" class="flex gap-2 w-full"></div>

      <!-- Playback Controls -->
      <div class="flex items-center justify-between gap-4">
        
        <div class="flex items-center gap-3">
          <button id="prevBtn" onclick="prevScene()" class="p-2.5 rounded-full hover:bg-stone-800 text-stone-300 transition" title="Previous Scene">
            ⏮
          </button>
          
          <button id="playBtn" onclick="togglePlay()" class="w-12 h-12 rounded-full bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold flex items-center justify-center text-xl shadow-lg transition transform active:scale-95" title="Play / Pause">
            ▶
          </button>

          <button id="nextBtn" onclick="nextScene()" class="p-2.5 rounded-full hover:bg-stone-800 text-stone-300 transition" title="Next Scene">
            ⏭
          </button>
        </div>

        <!-- Audio Progress Bar -->
        <div class="flex-1 flex items-center gap-3">
          <span id="currentTime" class="text-xs text-stone-400 font-mono w-10 text-right">0:00</span>
          <div class="flex-1 bg-stone-800 h-2 rounded-full overflow-hidden cursor-pointer relative" onclick="seekAudio(event)">
            <div id="progressBar" class="bg-amber-500 h-full w-0 transition-all duration-100"></div>
          </div>
          <span id="durationTime" class="text-xs text-stone-400 font-mono w-10">0:00</span>
        </div>

        <!-- Auto-Play Next Toggle -->
        <label class="flex items-center gap-2 cursor-pointer text-xs text-stone-400 select-none">
          <input type="checkbox" id="autoAdvance" checked class="accent-amber-500 w-4 h-4 rounded">
          Auto-advance Scenes
        </label>

      </div>
    </footer>

  </div>

  <!-- Audio Element -->
  <audio id="audioPlayer"></audio>

  <script>
    const scenes = {scenes_json};
    let currentIdx = 0;
    const audio = document.getElementById('audioPlayer');
    const playBtn = document.getElementById('playBtn');
    const progressBar = document.getElementById('progressBar');
    const autoAdvance = document.getElementById('autoAdvance');

    function renderScene(idx) {{
      if (idx < 0 || idx >= scenes.length) return;
      currentIdx = idx;
      const s = scenes[idx];

      // Update Texts
      document.getElementById('sceneBadge').innerText = `${{idx + 1}} / ${{scenes.length}}`;
      document.getElementById('narrationText').innerText = s.narration_text;
      document.getElementById('manuscriptExcerpt').innerText = s.manuscript_excerpt;
      document.getElementById('imagePromptText').innerText = '🎨 Scene visual: ' + s.visual_prompt;

      // Update Images
      const img = document.getElementById('sceneImage');
      img.classList.add('opacity-0');
      img.src = s.image_url;
      document.getElementById('backdrop').style.backgroundImage = `url('${{s.image_url}}')`;

      // Update Timeline Indicators
      renderTimeline();

      // Load Audio
      if (s.audio_base64) {{
        audio.src = "data:audio/mp3;base64," + s.audio_base64;
        audio.load();
      }} else {{
        audio.removeAttribute('src');
      }}
    }}

    function renderTimeline() {{
      const container = document.getElementById('sceneTimeline');
      container.innerHTML = '';
      scenes.forEach((s, i) => {{
        const bar = document.createElement('div');
        bar.className = `flex-1 h-2 rounded-full cursor-pointer transition-all ${{
          i === currentIdx ? 'bg-amber-500' : (i < currentIdx ? 'bg-amber-800/80' : 'bg-stone-800')
        }}`;
        bar.onclick = () => {{
          renderScene(i);
          playAudio();
        }};
        bar.title = `Jump to Scene ${{i + 1}}`;
        container.appendChild(bar);
      }});
    }}

    function togglePlay() {{
      if (audio.paused) {{
        playAudio();
      }} else {{
        audio.pause();
        playBtn.innerText = '▶';
      }}
    }}

    function playAudio() {{
      if (audio.src) {{
        audio.play().then(() => {{
          playBtn.innerText = '⏸';
        }}).catch(e => console.error("Play error:", e));
      }}
    }}

    function prevScene() {{
      if (currentIdx > 0) {{
        renderScene(currentIdx - 1);
        playAudio();
      }}
    }}

    function nextScene() {{
      if (currentIdx < scenes.length - 1) {{
        renderScene(currentIdx + 1);
        playAudio();
      }}
    }}

    function seekAudio(e) {{
      if (!audio.duration) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const pos = (e.clientX - rect.left) / rect.width;
      audio.currentTime = pos * audio.duration;
    }}

    audio.ontimeupdate = () => {{
      if (audio.duration) {{
        const pct = (audio.currentTime / audio.duration) * 100;
        progressBar.style.width = pct + '%';
        document.getElementById('currentTime').innerText = formatTime(audio.currentTime);
        document.getElementById('durationTime').innerText = formatTime(audio.duration);
      }}
    }};

    audio.onended = () => {{
      playBtn.innerText = '▶';
      if (autoAdvance.checked && currentIdx < scenes.length - 1) {{
        nextScene();
      }}
    }};

    function formatTime(secs) {{
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return `${{m}}:${{s < 10 ? '0' : ''}}${{s}}`;
    }}

    // Initial render
    if (scenes.length > 0) {{
      renderScene(0);
    }}
  </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path
