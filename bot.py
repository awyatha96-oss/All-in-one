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

# Channels
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}
user_state = {}
last_msg_ids = {}

# --- [3] REPLY KEYBOARD MENU (စာရိုက်သည့်နေရာမှ ခလုတ်များ) ---
def get_reply_keyboard(lang):
    if lang == "mm":
        return [
            ["📥 Video Downloader"],
            ["🗣 Text To Speech", "🔠 Translation"],
            ["📝 YouTube Transcript", "🌐 Languages"],
            ["📩 Contact Admin", "❓ Help"]
        ]
    return [
        ["📥 Video Downloader"],
        ["🗣 TTS", "🔠 Translation"],
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

# --- [4] MAIN HANDLERS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    await cleanup(event.chat_id, uid)
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    sent = await event.respond("Choose Language / ဘာသာစကား ရွေးချယ်ပါ -", buttons=btns)
    last_msg_ids[uid] = sent.id

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup_lang(event):
    uid = event.sender_id
    lang = event.pattern_match.group(1).decode()
    user_lang[uid] = lang
    await cleanup(event.chat_id, uid)
    sent = await event.respond("🌟 **Menu Activated!**", buttons=get_reply_keyboard(lang))
    last_msg_ids[uid] = sent.id

@client.on(events.NewMessage)
async def handle_input(event):
    uid = event.sender_id
    text = event.text
    if text.startswith('/'): return

    # Menu Button Clicks
    if "Video Downloader" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_link"
        sent = await event.respond("🔗 YouTube/TikTok Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "Transcript" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_script"
        sent = await event.respond("📝 YouTube Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif uid in user_state:
        state = user_state[uid]
        await cleanup(event.chat_id, uid)
        
        if state == "waiting_script":
            try:
                # Video ID ထုတ်ယူခြင်း
                vid_id = text.split("v=")[1].split("&")[0] if "v=" in text else text.split("/")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                full_text = " ".join([i['text'] for i in transcript])
                await event.respond(f"📝 **Transcript:**\n\n{full_text[:3000]}")
            except:
                await event.respond("❌ Transcript မရနိုင်ပါ (စာတန်းမပါတာ ဖြစ်နိုင်ပါတယ်)")
        
        user_state[uid] = None

print("Bot is started with Web Service Fix...")
client.run_until_disconnected()
