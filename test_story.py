from storyteller_engine import ManuscriptStorytellerEngine

engine = ManuscriptStorytellerEngine()
sample = "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत। अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्॥"
print("Processing sample manuscript...")
res = engine.process_story(sample, target_lang="hi-IN")
print("Story Title:", res.get("story_title"))
print("Scenes count:", len(res.get("scenes", [])))

for s in res.get("scenes", []):
    print(f"Scene {s['scene_id']}:")
    print(f"  Narration: {s['narration_text']}")
    print(f"  Audio bytes: {len(s['audio_base64'])} chars base64")
    print(f"  Image URL: {s['image_url'][:60]}...")

engine.generate_html_player(res, "sample_story_player.html")
print("Generated sample_story_player.html successfully!")
