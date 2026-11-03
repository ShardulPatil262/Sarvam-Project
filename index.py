import sys
import json
import os
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure project root is in python path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from storyteller_engine import ManuscriptStorytellerEngine, SUPPORTED_LANGUAGES

engine_instance = None

def get_engine():
    global engine_instance
    if engine_instance is None:
        engine_instance = ManuscriptStorytellerEngine()
    return engine_instance

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if "/languages" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SUPPORTED_LANGUAGES).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "online",
                "service": "Sarvam AI Manuscript Storyteller API"
            }).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            params = json.loads(body)
            manuscript = params.get("manuscript", "")
            target_lang = params.get("target_language", "hi-IN")
            speaker = params.get("speaker", None)

            if not manuscript.strip():
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Manuscript text is required"}).encode("utf-8"))
                return

            eng = get_engine()
            result = eng.process_story(manuscript, target_lang=target_lang, speaker=speaker)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        except Exception as e:
            traceback.print_exc()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

app = handler
application = handler

