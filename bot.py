import os
import asyncio
import threading
import http.server
import socketserver
import edge_tts
from telethon import TelegramClient, events, Button
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL

# --- [1] RENDER PORT BINDING FIX ---
def run_dummy_server():
    # Render ကပေးတဲ့ PORT ကိုယူမယ်၊ မရှိရင် 8080 သုံးမယ်
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    # Port ကို Bind လုပ်ပြီး Render ရဲ့ စစ်ဆေးမှုကို ကျော်ဖြတ်ရန်
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Dummy Server started at port {port}")
        httpd.serve_forever()

# Background thread အနေနဲ့ Server ကိုပတ်ထားမယ်
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

YOUTUBE_URL = "https://www.youtube.com/@VibeFootyTV"
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]
FOLDER_LINK = "https://t.me/addlist/0wjAKED6UWk4MzE1"

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}  
user_state = {} 
temp_data = {}  
user_usage_count = {}

# --- [3] STRINGS & BUTTONS ---
STRINGS = {
    "en": {
        "intro": "👋 **Welcome!**\nThis is your All-in-One Bot. Select a service below!",
        "sub_msg": "⚠️ **Subscription Required!**\nPlease join our channels and folder to continue.",
        "wait": "Processing... Please wait."
    },
    "mm": {
        "intro": "👋 **မင်္ဂလာပါ!**\nဒါကတော့ ဝန်ဆောင်မှုစုံလင်တဲ့ All-in-One Bot ဖြစ်ပါတယ်။ စတင်ရန် Menu မှ ရွေးချယ်ပါ။",
        "sub_msg": "⚠️ **Channel Join ရန်လိုအပ်ပါသည်!**\nရှေ့ဆက်ရန် YouTube နှင့် Folder ကို Join ပေးပါ။",
        "wait": "ခဏစောင့်ပါ... လုပ်ဆောင်နေပါတယ်။"
    }
}

def get_main_buttons(lang):
    return [
        [Button.inline("🌐 Languages", b"lang"), Button.inline("📥 Downloader", b"down")],
        [Button.inline("📝 Transcript", b"script"), Button.inline("🔠 Translation", b"trans")],
        [Button.inline("🗣 Text To Speech", b"tts")]
    ]

# --- [4] CORE FUNCTIONS ---
async def is_subscribed(user_id):
    try:
        for ch in PUBLIC_CHANNELS:
            p = await client.get_permissions(ch, user_id)
            if not p: return False
        return True
    except:
        return False

# --- [5] EVENT HANDLERS ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    await event.respond("Select Language / ဘာသာစကား ရွေးချယ်ပါ -", buttons=btns)

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup_lang(event):
    lang = event.pattern_match.group(1).decode()
    user_lang[event.sender_id] = lang
    await event.edit(STRINGS[lang]["intro"], buttons=get_main_buttons(lang))

@client.on(events.CallbackQuery(data=b"down"))
async def down_menu(event):
    uid = event.sender_id
    # Force Sub Check
    if user_usage_count.get(uid, 0) >= 1 and not await is_subscribed(uid):
        lang = user_lang.get(uid, "en")
        btns = [[Button.url("❤️ YouTube", YOUTUBE_URL)], [Button.url("📁 Join Folder", FOLDER_LINK)], [Button.inline("✅ Done", b"check_sub")]]
        return await event.respond(STRINGS[lang]["sub_msg"], buttons=btns)
    
    user_state[uid] = "waiting_link"
    msg = "Send Video Link (YT/TT):" if user_lang.get(uid) == "en" else "ဗီဒီယို Link ပို့ပေးပါ။"
    await event.edit(msg)

@client.on(events.NewMessage)
async def handle_text(event):
    uid = event.sender_id
    if event.text.startswith('/'): return
    state = user_state.get(uid)

    if state == "waiting_link":
        url = event.text
        user_usage_count[uid] = user_usage_count.get(uid, 0) + 1
        if "tiktok.com" in url:
            await event.respond("📥 TikTok Detected... Downloading 1080p.")
            await download_video(event, url, "bestvideo+bestaudio/best")
        else:
            btns = [[Button.inline("🎬 360p", f"y_{url}_360"), Button.inline("🎬 720p", f"y_{url}_720")],
                    [Button.inline("🎬 1080p", f"y_{url}_1080"), Button.inline("🎵 Audio", f"y_{url}_audio")]]
            await event.respond("Select YouTube Quality:", buttons=btns)
        user_state[uid] = None

async def download_video(event, url, fmt):
    path = f"vid_{event.sender_id}.mp4"
    opts = {'format': fmt, 'outtmpl': path, 'quiet': True, 'merge_output_format': 'mp4'}
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        await event.client.send_file(event.chat_id, path, caption="Success!")
    except Exception as e:
        await event.respond(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(path): os.remove(path)

@client.on(events.CallbackQuery(data=b"check_sub"))
async def verify_sub(event):
    if await is_subscribed(event.sender_id):
        lang = user_lang.get(event.sender_id, "en")
        await event.edit("✅ Success!", buttons=get_main_buttons(lang))
    else:
        await event.answer("❌ Please join channels first!", alert=True)

# Start the Bot
print("Bot is starting on Render Web Service...")
client.run_until_disconnected()
