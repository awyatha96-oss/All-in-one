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

# --- [1] RENDER PORT FIX (Web Service Error ရှင်းရန်) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIG ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}
user_state = {}
last_msg_ids = {}

# --- [3] REPLY KEYBOARD (မင်းပြထားတဲ့ ပုံစံအတိုင်း Menu စီထားခြင်း) ---
def get_reply_keyboard(lang):
    # စာရိုက်သည့်နေရာ၏ အပေါ်တွင် ကပ်နေမည့် ခလုတ်များ
    return [
        ["📥 Video Downloader"],
        ["🗣 Text To Speech", "🔠 Translation"],
        ["📝 YouTube Transcript", "🌐 Languages"],
        ["📩 Contact Admin", "❓ Help"]
    ]

async def cleanup(chat_id, user_id):
    if user_id in last_msg_ids:
        try:
            await client.delete_messages(chat_id, last_msg_ids[user_id])
            del last_msg_ids[user_id]
        except: pass

async def is_subscribed(user_id):
    try:
        for ch in PUBLIC_CHANNELS:
            p = await client.get_permissions(ch, user_id)
            if not p: return False
        return True
    except: return False

# --- [4] EVENT HANDLERS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    await cleanup(event.chat_id, uid)
    # အစပိုင်းတွင် Language ရွေးခိုင်းမည်
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    sent = await event.respond("ဘာသာစကား ရွေးချယ်ပါ / Choose Language:", buttons=btns)
    last_msg_ids[uid] = sent.id

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup_lang(event):
    uid = event.sender_id
    lang = event.pattern_match.group(1).decode()
    user_lang[uid] = lang
    await cleanup(event.chat_id, uid)
    # မင်းပြထားတဲ့အတိုင်း Menu ခလုတ်များကို အသက်သွင်းခြင်း
    sent = await event.respond(
        "✅ **Main Menu Activated!**\nအောက်က Menu ခလုတ်တွေကို သုံးနိုင်ပါပြီ။",
        buttons=get_reply_keyboard(lang)
    )
    last_msg_ids[uid] = sent.id

@client.on(events.NewMessage)
async def handle_menu_clicks(event):
    uid = event.sender_id
    text = event.text
    if text.startswith('/'): return

    # --- Menu Button Actions ---
    if "Video Downloader" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_link"
        sent = await event.respond("🔗 YouTube/TikTok Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "Translation" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_trans"
        sent = await event.respond("🔠 ဘာသာပြန်လိုတဲ့ စာသားကို ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "Transcript" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_script"
        sent = await event.respond("📝 YouTube Video Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    # --- Input Processing ---
    elif uid in user_state:
        state = user_state[uid]
        await cleanup(event.chat_id, uid)
        
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
                await event.respond("❌ Transcript မရနိုင်ပါ။")

        user_state[uid] = None

print("Bot is starting with Reply Keyboard...")
client.run_until_disconnected()
