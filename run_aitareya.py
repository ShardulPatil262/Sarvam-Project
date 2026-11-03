import json
from storyteller_engine import ManuscriptStorytellerEngine

engine = ManuscriptStorytellerEngine()

scenes_def = [
    {
        "scene_id": 1,
        "manuscript_excerpt": "ऐतरेय आरण्यकम्\nआत्मा वा इदमेक एवाग्र आसीत् ।",
        "narration_text": "सृष्टि के आरंभ से भी पूर्व, केवल एक ही परमात्मा—परम चेतना आत्मा का अस्तित्व था। काल, अंतरिक्ष या दिशाओं का भी कोई नामोनिशान न था।",
        "visual_prompt": "A primordial golden cosmic aura representing the Supreme Atman, glowing peacefully in the center of an infinite deep celestial void before creation, sacred ancient Vedic atmosphere, classical Indian miniature painting style, soft divine lighting"
    },
    {
        "scene_id": 2,
        "manuscript_excerpt": "नान्यत्किञ्चन मिषत् ।",
        "narration_text": "उस महाशून्य में न कोई दूसरा प्राणी था, न कोई स्पंदन, न ही कोई आँख जो पलक भी झपका सके। चारों ओर केवल असीम, ध्यानमग्न नीरवता छाई थी।",
        "visual_prompt": "Vast tranquil cosmic ocean under a starlit night sky, absolute silence and stillness, deep indigo and sapphire mists, transcendental calm, no living beings yet, ancient philosophical painting, cinematic moody lighting"
    },
    {
        "scene_id": 3,
        "manuscript_excerpt": "स ईक्षत लोकान्नु सृजा इति ॥",
        "narration_text": "तब उस परम चेतना ने संकल्प किया—'मैं अब इन दिव्य लोकों की रचना करूँ!' और इस दिव्य विचार से संपूर्ण ब्रह्मांड का विस्तार प्रारंभ हुआ।",
        "visual_prompt": "Cosmic dawn of creation, brilliant bursts of divine light expanding into new celestial realms, earth, skies, stars, and radiant galaxies forming, epic cosmic creation, classical Indian miniature oil painting, dramatic golden rays"
    }
]

processed_scenes = []
for s in scenes_def:
    print(f"Synthesizing Audio for Scene {s['scene_id']} via Sarvam Bulbul:v3...")
    audio_b64 = engine.synthesize_speech(s["narration_text"], lang_code="hi-IN", speaker="roopa")
    img_url = engine.get_image_url(s["visual_prompt"], seed=300 + s["scene_id"] * 57)
    processed_scenes.append({
        "scene_id": s["scene_id"],
        "manuscript_excerpt": s["manuscript_excerpt"],
        "narration_text": s["narration_text"],
        "visual_prompt": s["visual_prompt"],
        "image_url": img_url,
        "audio_base64": audio_b64
    })
    print(f"  Scene {s['scene_id']} Audio generated: {len(audio_b64)} chars base64")

story_data = {
    "story_title": "ऐतरेय आरण्यकम्: सृष्टि का प्रथम संकल्प",
    "target_language": "hi-IN",
    "target_language_name": "Hindi (हिंदी)",
    "scenes": processed_scenes
}

with open("aitareya_complete_story.json", "w", encoding="utf-8") as f:
    json.dump(story_data, f, ensure_ascii=False, indent=2)

engine.generate_html_player(story_data, "aitareya_story_player.html")
print("Successfully generated aitareya_story_player.html!")
