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

# --- [1] RENDER WEB SERVICE PORT BINDING FIX ---
# Render တွင် Web Service အဖြစ် run ရန် ဤအပိုင်းကို မဖြစ်မနေ ထည့်ရပါမည်
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Dummy server running on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
# သင်၏ ကိုယ်ပိုင် API ID, Hash နှင့် Token များကို ဤနေရာတွင် စစ်ဆေးပါ
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

# Bot Name
BOT_NAME = "OmniVerse Bot"

client = TelegramClient('omniverse_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_state = {}

# --- [3] REPLY KEYBOARD SETUP ---
def get_main_menu():
    # မင်းတောင်းဆိုထားတဲ့ Layout အတိုင်း Row 3 ခု စီထားသည်
    buttons = [
        ["🎥 Video Downloader", "📝 Transcript"],      # Row 1
        ["🌍 Translation", "🗣️ Text To Speech"],       # Row 2
        ["🌐 Language"]                               # Row 3
    ]
    # resize=True: ဖုန်း Screen နှင့် အံကိုက်ဖြစ်စေရန်
    # placeholder: စာရိုက်သည့်နေရာတွင် ပေါ်မည့် လမ်းညွှန်စာသား
    return client.build_reply_markup(
        buttons, 
        resize=True, 
        placeholder="အသုံးပြုလိုသည့် Feature ကို ရွေးပါ"
    )

# --- [4] MESSAGE HANDLERS ---

# /start command လက်ခံရရှိပါက Keyboard ကို ချက်ချင်း ပို့ပေးမည့် Logic
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        f"🌟 **{BOT_NAME} မှ ကြိုဆိုပါတယ်** 🌟\n\nလုပ်ဆောင်ချက်များကို စတင်ရန် အောက်ပါ Menu မှ ခလုတ်များကို နှိပ်ပါ။",
        buttons=get_main_menu()
    )

# Menu ခလုတ်များနှိပ်ခြင်းနှင့် အချက်အလက်လက်ခံခြင်း Logic
@client.on(events.NewMessage)
async def handle_all_logic(event):
    uid = event.sender_id
    text = event.text

    # Command များဖြစ်ပါက ကျော်သွားမည်
    if text.startswith('/'): return

    # --- (A) Menu Button Click Handler ---
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

    elif text == "🌐 Language":
        await event.respond("🌐 ဘာသာစကား ရွေးချယ်မှု စနစ်ကို မကြာမီ ထည့်သွင်းပါမည်။")

    # --- (B) Processing User Data (MessageHandler Logic) ---
    elif uid in user_state:
        state = user_state[uid]
        
        if state == "waiting_trans":
            try:
                res = GoogleTranslator(source='auto', target='my').translate(text)
                await event.respond(f"📝 **ဘာသာပြန်ချက်:**\n\n{res}")
            except Exception as e:
                await event.respond(f"❌ Error: {str(e)}")
        
        elif state == "waiting_script":
            try:
                # YouTube Video ID ကို ထုတ်ယူခြင်း
                vid_id = text.split("v=")[1].split("&")[0] if "v=" in text else text.split("/")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                full_text = " ".join([i['text'] for i in transcript])
                await event.respond(f"📝 **Transcript:**\n\n{full_text[:3000]}")
            except:
                await event.respond("❌ Transcript မရနိုင်ပါ။ YouTube Link မှန်ကန်ပါစေ။")

        elif state == "waiting_tts":
            status_msg = await event.respond("🗣️ အသံဖိုင် ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ။")
            path = f"tts_{uid}.mp3"
            try:
                communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
                await communicate.save(path)
                await client.send_file(event.chat_id, path, caption="✅ TTS ပြီးစီးပါပြီ")
            except Exception as e:
                await event.respond(f"❌ Error: {str(e)}")
            finally:
                await status_msg.delete()
                if os.path.exists(path): os.remove(path)

        # အလုပ်ပြီးပါက state ကို Reset ချပါမည်
        user_state[uid] = None

print(f"--- {BOT_NAME} Started Successfully ---")
client.run_until_disconnected()
