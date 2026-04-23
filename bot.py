import os
import asyncio
import threading
import http.server
import socketserver
from telethon import TelegramClient, events
from deep_translator import GoogleTranslator
from youtube_transcript_api import YouTubeTranscriptApi
import edge_tts

# --- [1] RENDER WEB SERVICE PORT BINDING FIX ---
# Render တွင် 'Port scan timeout' error မတက်စေရန် port ကို နားထောင်ပေးရပါမည်
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
# သင်၏ API ID, API HASH နှင့် BOT TOKEN တို့ကို အောက်တွင် ထည့်သွင်းပါ
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

# Bot နာမည်ကို SwiftTool Bot ဟု သတ်မှတ်ပေးထားပါသည်
client = TelegramClient('swift_tool_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_state = {}

# --- [3] REPLY KEYBOARD LAYOUT ---
def get_main_menu():
    # မင်းတောင်းဆိုထားတဲ့အတိုင်း Feature ခလုတ် ၅ ခုကို Layout ၃ တန်း စီစဉ်ထားပါသည်
    buttons = [
        ["🎥 Video Downloader", "📝 Transcript"],      # Row 1
        ["🌍 Translation", "🗣️ Text To Speech"],       # Row 2
        ["🌐 Language"]                               # Row 3
    ]
    # resize=True: ဖုန်း screen နှင့် အတော်ဖြစ်အောင် အရွယ်အစားညှိပေးပါသည်
    # placeholder: စာရိုက်သည့်နေရာတွင် လမ်းညွှန်စာသား ပေါ်စေပါသည်
    return client.build_reply_markup(
        buttons, 
        resize=True, 
        placeholder="အသုံးပြုလိုသည့် Feature ကို ရွေးပါ"
    )

# --- [4] MESSAGE HANDLERS ---

# /start command လက်ခံရရှိပါက Keyboard ကို ချက်ချင်း ပို့ပေးမည်
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "🌟 **SwiftTool Bot မှ ကြိုဆိုပါတယ်** 🌟\n\nအောက်ပါ Menu ခလုတ်များကို အသုံးပြု၍ Feature များကို စတင်နိုင်ပါပြီ။",
        buttons=get_main_menu()
    )

# Menu ခလုတ်များ၏ လုပ်ဆောင်ချက်များကို ကိုင်တွယ်ခြင်း
@client.on(events.NewMessage)
async def handle_all_input(event):
    uid = event.sender_id
    text = event.text

    if text.startswith('/'): return

    # --- (A) Menu Button Selection Logic ---
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
        await event.respond("🌐 ဘာသာစကား ရွေးချယ်မှု စနစ်ကို မကြာမီ ထည့်သွင်းပေးပါမည်။")

    # --- (B) Processing Logic for each Feature ---
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
                # Video ID ကို link မှ ခွဲထုတ်ခြင်း
                vid_id = text.split("v=")[1].split("&")[0] if "v=" in text else text.split("/")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                full_text = " ".join([i['text'] for i in transcript])
                await event.respond(f"📝 **Transcript ရလဒ်:**\n\n{full_text[:3000]}")
            except:
                await event.respond("❌ Transcript မရနိုင်ပါ။ YouTube Link မှန်ကန်ပါစေ။")

        elif state == "waiting_tts":
            path = f"tts_{uid}.mp3"
            try:
                communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
                await communicate.save(path)
                await client.send_file(event.chat_id, path, caption="✅ TTS ပြီးစီးပါပြီ")
            finally:
                if os.path.exists(path): os.remove(path)

        # လုပ်ဆောင်ချက်ပြီးဆုံးပါက state ကို ပြန်ဖျက်ပါမည်
        user_state[uid] = None

print("SwiftTool Bot is starting...")
client.run_until_disconnected()
