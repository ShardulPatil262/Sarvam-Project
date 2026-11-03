import os
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from storyteller_engine import ManuscriptStorytellerEngine, SUPPORTED_LANGUAGES

PORT = 8000
engine = None

def get_engine():
    global engine
    if engine is None:
        engine = ManuscriptStorytellerEngine()
    return engine

STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sarvam Manuscript Storyteller Studio</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-stone-950 text-stone-100 min-h-screen font-sans selection:bg-amber-600 selection:text-white">

  <!-- Header -->
  <header class="border-b border-stone-800 bg-stone-900/60 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <span class="text-3xl">📜</span>
      <div>
        <h1 class="text-xl font-bold font-serif text-amber-100">Sarvam Manuscript Storyteller</h1>
        <p class="text-xs text-stone-400">Transcribe & Translate Manuscripts into Narrated Audio with Synced Visuals</p>
      </div>
    </div>
    <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      Sarvam Bulbul & 105B Connected
    </span>
  </header>

  <div class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
    
    <!-- Left Column: Input Form & Controls -->
    <div class="lg:col-span-5 space-y-6">
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-6 shadow-xl space-y-5">
        <h2 class="text-lg font-serif font-semibold text-amber-200 flex items-center gap-2">
          <span>✍️</span> Manuscript Input
        </h2>

        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
            Paste Manuscript Text (Sanskrit, Old Tamil, Pali, Hindi, English, etc.)
          </label>
          <textarea id="manuscriptInput" rows="7" class="w-full bg-stone-950 border border-stone-700 rounded-xl p-3.5 text-stone-200 text-sm focus:border-amber-500 focus:outline-none transition resize-none font-mono" placeholder="Enter ancient manuscript passage, verse, or folktale excerpt here..."></textarea>
        </div>

        <!-- Sample Quick Presets -->
        <div class="space-y-1.5">
          <span class="text-xs text-stone-400 font-medium">Or load a sample manuscript:</span>
          <div class="flex flex-wrap gap-2">
            <button onclick="loadSample('gita')" class="text-xs px-2.5 py-1 rounded-lg bg-stone-800 hover:bg-stone-700 text-amber-300 border border-stone-700 transition">
              Sanskrit: Bhagavad Gita
            </button>
            <button onclick="loadSample('panchatantra')" class="text-xs px-2.5 py-1 rounded-lg bg-stone-800 hover:bg-stone-700 text-amber-300 border border-stone-700 transition">
              Sanskrit / Hindi: Panchatantra
            </button>
            <button onclick="loadSample('silappadikaram')" class="text-xs px-2.5 py-1 rounded-lg bg-stone-800 hover:bg-stone-700 text-amber-300 border border-stone-700 transition">
              Tamil Epic: Silappadikaram
            </button>
          </div>
        </div>

        <!-- Language & Voice Selection -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
              Narration Language
            </label>
            <select id="targetLang" onchange="updateVoices()" class="w-full bg-stone-950 border border-stone-700 rounded-xl p-2.5 text-sm text-stone-200 focus:border-amber-500 focus:outline-none">
              <option value="hi-IN" selected>Hindi (हिंदी)</option>
              <option value="en-IN">English (Indian)</option>
              <option value="bn-IN">Bengali (বাংলা)</option>
              <option value="ta-IN">Tamil (தமிழ்)</option>
              <option value="te-IN">Telugu (తెలుగు)</option>
              <option value="kn-IN">Kannada (ಕನ್ನಡ)</option>
              <option value="mr-IN">Marathi (मराठी)</option>
              <option value="gu-IN">Gujarati (ગુજરાતી)</option>
              <option value="pa-IN">Punjabi (ਪੰਜਾਬੀ)</option>
              <option value="ml-IN">Malayalam (മലയാളം)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
              Voice Narrator
            </label>
            <select id="voiceSpeaker" class="w-full bg-stone-950 border border-stone-700 rounded-xl p-2.5 text-sm text-stone-200 focus:border-amber-500 focus:outline-none">
              <option value="roopa">Roopa (Warm Narrative)</option>
              <option value="shubh">Shubh (Dramatic Story)</option>
              <option value="priya">Priya (Expressive)</option>
              <option value="aditya">Aditya (Classical Male)</option>
            </select>
          </div>
        </div>

        <button id="generateBtn" onclick="generateStory()" class="w-full py-3.5 px-4 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-stone-950 font-bold rounded-xl shadow-lg transition flex items-center justify-center gap-2 transform active:scale-[0.99]">
          <span id="btnIcon">✨</span>
          <span id="btnText">Synthesize Narration & Visual Scenes</span>
        </button>

      </div>
    </div>

    <!-- Right Column: Interactive Storyboard & Audio Player -->
    <div class="lg:col-span-7">
      
      <!-- Placeholder when not generated -->
      <div id="emptyState" class="h-full min-h-[460px] border-2 border-dashed border-stone-800 rounded-2xl flex flex-col items-center justify-center p-8 text-center bg-stone-900/30">
        <span class="text-5xl mb-4">🎭</span>
        <h3 class="text-lg font-serif font-medium text-stone-300">Ready to Narrate Your Manuscript</h3>
        <p class="text-sm text-stone-500 max-w-sm mt-1">
          Paste manuscript text on the left and select your desired language. The model will translate, voice the story, and generate contextual visual scenes.
        </p>
      </div>

      <!-- Live Player (Hidden initially) -->
      <div id="playerContainer" class="hidden bg-stone-900/90 border border-stone-800 rounded-2xl p-6 shadow-2xl space-y-6">
        
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <div>
            <h3 id="displayStoryTitle" class="text-xl font-serif font-bold text-amber-200"></h3>
            <span id="displayLangBadge" class="text-xs text-amber-400 font-medium"></span>
          </div>
          <span id="liveSceneBadge" class="text-xs font-mono bg-stone-800 px-3 py-1 rounded-full text-stone-300">Scene 1 / 1</span>
        </div>

        <!-- Visual Art Frame -->
        <div class="aspect-video w-full rounded-xl overflow-hidden border border-amber-600/30 shadow-2xl relative bg-stone-950 group">
          <img id="activeSceneImage" src="" alt="Contextual Scene Illustration" class="w-full h-full object-cover transition-opacity duration-500">
          <div class="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent"></div>
          
          <div class="absolute bottom-3 left-3 right-3">
            <p id="activePromptTag" class="text-[11px] text-stone-300 italic line-clamp-2 bg-stone-950/80 backdrop-blur px-3 py-1.5 rounded-lg border border-stone-800"></p>
          </div>
        </div>

        <!-- Synchronized Subtitles -->
        <div class="bg-stone-950/80 border border-stone-800 rounded-xl p-4 relative">
          <span class="text-[10px] font-semibold uppercase tracking-wider text-amber-400 block mb-1">Spoken Story Narration</span>
          <p id="activeNarrationText" class="text-lg font-serif text-amber-100 leading-relaxed"></p>
          <div class="mt-3 pt-3 border-t border-stone-800/80">
            <span class="text-[10px] uppercase tracking-wider text-stone-500 block mb-0.5">Original Manuscript Text</span>
            <p id="activeManuscriptText" class="text-xs font-mono text-stone-400 italic"></p>
          </div>
        </div>

        <!-- Timeline Buttons -->
        <div id="timelineContainer" class="flex gap-2"></div>

        <!-- Controls -->
        <div class="flex items-center justify-between gap-4 pt-2">
          <div class="flex items-center gap-2">
            <button onclick="prevStoryScene()" class="p-2 rounded-lg bg-stone-800 hover:bg-stone-700 text-stone-200 text-sm">⏮ Prev</button>
            <button id="mainPlayBtn" onclick="toggleStoryPlay()" class="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold flex items-center gap-1.5 shadow-md">
              <span id="playIcon">▶</span> Play Audio
            </button>
            <button onclick="nextStoryScene()" class="p-2 rounded-lg bg-stone-800 hover:bg-stone-700 text-stone-200 text-sm">Next ⏭</button>
          </div>

          <audio id="liveAudio"></audio>

          <label class="flex items-center gap-2 cursor-pointer text-xs text-stone-400 select-none">
            <input type="checkbox" id="autoAdvanceToggle" checked class="accent-amber-500 w-4 h-4 rounded">
            Auto-advance scenes
          </label>
        </div>

      </div>

    </div>

  </div>

  <script>
    const SAMPLES = {
      gita: "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत। अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्॥ परित्राणाय साधूनां विनाशाय च दुष्कृताम्। धर्मसंस्थापनार्थाय सम्भवामि युगे युगे॥\\n\\nअर्जुन उवाच - कथं भीष्ममहं संख्ये द्रोणं च मधुसूदन। इषुभिः प्रतियोत्स्यामि पूजार्हावरिसूदन॥",
      panchatantra: "अस्ति दक्षिणापथे महिलानाम नगरम्। तत्र वर्धमानको नाम वणिक्पुत्रः प्रतिवसति स्म। तस्य धर्मोपार्जिते विपुलवित्ते संजातेऽपि मतिरुदपद्यत - अर्थागमे न सन्तोषः कार्यः।\\n\\nततः स प्रचुरतरं पण्यमादाय मथुरां प्रति प्रस्थितः। मार्गे यमुनातीरे तस्य संजीवकनामा बलीवर्दः पङ्के निमग्नः।",
      silappadikaram: "வளநகர் சிலம்பொலி கேட்கும் புகார் நகரின் பெருவணிகன் மாசாத்துவான் மகன் கோவலன். அவன் மனைவி கற்பின் செல்வி கண்ணகி. விதிவசத்தால் மாதவியின் ஆடலரங்கில் மயங்கிப் பொருள் இழந்த கோவலன், மீண்டும் மனைவியிடம் அடைக்கலம் புகுந்து புதிய வாழ்வைத் தேடி மதுரை நோக்கிப் புறப்பட்டான்."
    };

    let storyScenes = [];
    let activeSceneIdx = 0;
    const audioEl = document.getElementById('liveAudio');

    function loadSample(key) {
      document.getElementById('manuscriptInput').value = SAMPLES[key];
    }

    function updateVoices() {
      const lang = document.getElementById('targetLang').value;
      const speakerSelect = document.getElementById('voiceSpeaker');
      speakerSelect.innerHTML = '';
      
      const speakersByLang = {
        'hi-IN': [['roopa', 'Roopa (Warm Narrative)'], ['shubh', 'Shubh (Dramatic Story)'], ['priya', 'Priya (Expressive)'], ['aditya', 'Aditya (Classical Male)']],
        'en-IN': [['shubh', 'Shubh (Narrator)'], ['ishita', 'Ishita (Gentle Story)'], ['roopa', 'Roopa (Warm)']],
        'ta-IN': [['gokul', 'Gokul (Tamil Narrator)'], ['vijay', 'Vijay (Expressive)'], ['shubh', 'Shubh']],
        'te-IN': [['kavitha', 'Kavitha (Telugu Storyteller)'], ['tarun', 'Tarun (Male Voice)'], ['pooja', 'Pooja']],
        'mr-IN': [['soham', 'Soham (Marathi Narrator)'], ['rupali', 'Rupali (Stories)'], ['shubh', 'Shubh']],
        'gu-IN': [['pooja', 'Pooja (Gujarati Narrator)'], ['shubh', 'Shubh']],
        'bn-IN': [['shubh', 'Shubh (Bengali Voice)'], ['roopa', 'Roopa']],
        'kn-IN': [['shubh', 'Shubh (Kannada Voice)'], ['roopa', 'Roopa']],
        'pa-IN': [['anand', 'Anand (Punjabi Narrator)'], ['shubh', 'Shubh']],
        'ml-IN': [['shubh', 'Shubh (Malayalam Voice)'], ['roopa', 'Roopa']]
      };

      const options = speakersByLang[lang] || [['shubh', 'Shubh'], ['roopa', 'Roopa']];
      options.forEach(([val, label]) => {
        const opt = document.createElement('option');
        opt.value = val;
        opt.innerText = label;
        speakerSelect.appendChild(opt);
      });
    }

    async function generateStory() {
      const manuscript = document.getElementById('manuscriptInput').value.trim();
      if (!manuscript) {
        alert("Please paste or type a manuscript passage first!");
        return;
      }

      const targetLang = document.getElementById('targetLang').value;
      const speaker = document.getElementById('voiceSpeaker').value;
      const btn = document.getElementById('generateBtn');
      const btnText = document.getElementById('btnText');
      const btnIcon = document.getElementById('btnIcon');

      btn.disabled = true;
      btn.classList.add('opacity-70');
      btnText.innerText = "Synthesizing Story & Visual Scenes via Sarvam AI...";
      btnIcon.innerText = "⏳";

      try {
        const response = await fetch('/api/process', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ manuscript, target_language: targetLang, speaker })
        });
        const data = await response.json();

        if (data.error) {
          alert("Error: " + data.error);
          return;
        }

        storyScenes = data.scenes || [];
        document.getElementById('displayStoryTitle').innerText = data.story_title || "Manuscript Story";
        document.getElementById('displayLangBadge').innerText = "Language: " + (data.target_language_name || targetLang);

        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('playerContainer').classList.remove('hidden');

        showScene(0);
        toggleStoryPlay();

      } catch (err) {
        alert("Failed to process story: " + err.message);
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-70');
        btnText.innerText = "Synthesize Narration & Visual Scenes";
        btnIcon.innerText = "✨";
      }
    }

    function showScene(idx) {
      if (idx < 0 || idx >= storyScenes.length) return;
      activeSceneIdx = idx;
      const s = storyScenes[idx];

      document.getElementById('liveSceneBadge').innerText = `Scene ${idx + 1} / ${storyScenes.length}`;
      document.getElementById('activeNarrationText').innerText = s.narration_text;
      document.getElementById('activeManuscriptText').innerText = s.manuscript_excerpt;
      document.getElementById('activePromptTag').innerText = '🎨 ' + s.visual_prompt;

      const img = document.getElementById('activeSceneImage');
      img.src = s.image_url;

      renderStudioTimeline();

      if (s.audio_base64) {
        audioEl.src = "data:audio/mp3;base64," + s.audio_base64;
        audioEl.load();
      }
    }

    function renderStudioTimeline() {
      const container = document.getElementById('timelineContainer');
      container.innerHTML = '';
      storyScenes.forEach((s, i) => {
        const b = document.createElement('div');
        b.className = `flex-1 h-2 rounded-full cursor-pointer transition-all ${
          i === activeSceneIdx ? 'bg-amber-500' : 'bg-stone-800 hover:bg-stone-700'
        }`;
        b.onclick = () => {
          showScene(i);
          playStoryAudio();
        };
        container.appendChild(b);
      });
    }

    function toggleStoryPlay() {
      if (audioEl.paused) {
        playStoryAudio();
      } else {
        audioEl.pause();
        document.getElementById('playIcon').innerText = '▶';
      }
    }

    function playStoryAudio() {
      if (audioEl.src) {
        audioEl.play().then(() => {
          document.getElementById('playIcon').innerText = '⏸';
        }).catch(e => console.log(e));
      }
    }

    function prevStoryScene() {
      if (activeSceneIdx > 0) {
        showScene(activeSceneIdx - 1);
        playStoryAudio();
      }
    }

    function nextStoryScene() {
      if (activeSceneIdx < storyScenes.length - 1) {
        showScene(activeSceneIdx + 1);
        playStoryAudio();
      }
    }

    audioEl.onended = () => {
      document.getElementById('playIcon').innerText = '▶';
      const autoAdv = document.getElementById('autoAdvanceToggle').checked;
      if (autoAdv && activeSceneIdx < storyScenes.length - 1) {
        nextStoryScene();
      }
    };
  </script>
</body>
</html>
"""

class StoryServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(STUDIO_HTML.encode("utf-8"))
        elif self.path == "/api/languages":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(SUPPORTED_LANGUAGES).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/process":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                params = json.loads(body)
                manuscript = params.get("manuscript", "")
                target_lang = params.get("target_language", "hi-IN")
                speaker = params.get("speaker", None)

                eng = get_engine()
                result = eng.process_story(manuscript, target_lang=target_lang, speaker=speaker)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, StoryServerHandler)
    print(f"Manuscript Storyteller server running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")

if __name__ == "__main__":
    run_server()
else:
    handler = StoryServerHandler
    app = handler
    application = handler

