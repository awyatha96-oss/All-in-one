import os
import asyncio
import threading
import http.server
import socketserver
from telethon import TelegramClient, events, Button
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL
import edge_tts
from youtube_transcript_api import YouTubeTranscriptApi

# --- [1] RENDER WEB SERVICE PORT FIX ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

# Bot နာမည်အသစ်
BOT_NAME = "OmniVerse Bot"

client = TelegramClient('omniverse_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_state = {}

# --- [3] REPLY KEYBOARD LAYOUT (3 Rows + Resize + Placeholder) ---
def get_main_menu():
    buttons = [
        ["🎥 Video Downloader", "📝 Transcript"],      # Row 1
        ["🌍 Translation", "🗣️ Text To Speech"],       # Row 2
        ["🌐 Language"]                               # Row 3
    ]
    return client.build_reply_markup(
        buttons, 
        resize=True,                                  # ဖုန်း Screen နှင့် အတော်ဖြစ်စေရန်
        placeholder="အသုံးပြုလိုသည့် Feature ကို ရွေးပါ"      # Placeholder စာသား
    )

# --- [4] MESSAGE HANDLERS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        f"🌟 **{BOT_NAME} မှ ကြိုဆိုပါတယ်** 🌟\n\nလုပ်ဆောင်ချက်များကို စတင်ရန် အောက်ပါ Menu မှ ခလုတ်များကို နှိပ်ပါ။",
        buttons=get_main_menu()
    )

@client.on(events.NewMessage)
async def handle_logic(event):
    uid = event.sender_id
    text = event.text

    if text.startswith('/'): return

    # --- Menu Button Clicks (MessageHandler Logic) ---
    if text == "🎥 Video Downloader":
        user_state[uid] = "waiting_video"
        await event.respond("📥 Video ဒေါင်းလုဒ်လုပ်ရန် **Link ပို့ပေးပါ**။")

    elif text == "📝 Transcript":
        user_state[uid] = "waiting_script"
        await event.respond("📝 Transcript ထုတ်ယူရန် YouTube **Link ပို့ပေးပါ**။")

    elif text == "🌍 Translation":
        user_state[uid] = "waiting_trans"
        await event.respond("🔠 ဘာသာပြန်ဆိုရန် **စာသားရိုက်ထည့်ပါ**။")

    elif text == "🗣️ Text To Speech":
        user_state[uid] = "waiting_tts"
        await event.respond("🗣️ အသံပြောင်းလဲရန် **စာသားရိုက်ထည့်ပါ**။")

    # --- Input Processing States ---
    elif uid in user_state:
        state = user_state[uid]
        
        if state == "waiting_trans":
            res = GoogleTranslator(source='auto', target='my').translate(text)
            await event.respond(f"📝 **ဘာသာပြန်ချက်:**\n\n{res}")
        
        elif state == "waiting_script":
            try:
                vid_id = text.split("v=")[1].split("&")[0] if "v=" in text else text.split("/")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                full_text = " ".join([i['text'] for i in transcript])
                await event.respond(f"📝 **Transcript:**\n\n{full_text[:3000]}")
            except:
                await event.respond("❌ Transcript မရနိုင်ပါ။ YouTube Link မှန်ကန်ပါစေ။")

        elif state == "waiting_tts":
            path = f"tts_{uid}.mp3"
            communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
            await communicate.save(path)
            await client.send_file(event.chat_id, path, caption="✅ TTS ပြီးစီးပါပြီ")
            os.remove(path)

        user_state[uid] = None

print(f"{BOT_NAME} is Live on Render...")
client.run_until_disconnected()
