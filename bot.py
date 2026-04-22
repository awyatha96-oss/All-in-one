import os
import asyncio
import threading
import http.server
import socketserver
import edge_tts
from telethon import TelegramClient, events, Button
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL

# --- [1] RENDER PORT FIX (Dummy Server) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

# YouTube Links
YT_LINK_1 = "https://www.youtube.com/@VibeFootyTV"
YT_LINK_2 = "http://googleusercontent.com/youtube.com/another_yt" # မင်းရဲ့ ဒုတိယ YT Link

# Telegram Links
FOLDER_LINK = "https://t.me/addlist/0wjAKED6UWk4MzE1"
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"] 

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}  
user_state = {} 
user_usage_count = {}

# --- [3] UI MENUS ---

def get_main_buttons(lang):
    return [
        [Button.inline("📥 Video Downloader", b"down")],
        [Button.inline("🗣 Text To Speech", b"tts"), Button.inline("🔠 Translation", b"trans")],
        [Button.inline("📝 YouTube Transcript", b"script"), Button.inline("🌐 Languages", b"lang")],
        [Button.inline("📩 Contact Admin", b"contact"), Button.inline("❓ Help", b"help")]
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

async def check_force_sub(event):
    uid = event.sender_id
    if user_usage_count.get(uid, 0) >= 1:
        if not await is_subscribed(uid):
            lang = user_lang.get(uid, "en")
            msg = "⚠️ **Please join our channels and folder to continue.**"
            if lang == "mm":
                msg = "⚠️ **ရှေ့ဆက်ရန် ကျွန်ုပ်တို့၏ YouTube နှင့် Channel များကို Join ပေးပါ။**"

            sub_btns = [
                # YouTube ခလုတ်နှစ်ခု ဘေးချင်းယှဉ်
                [
                    Button.url("❤️ 1# YouTube", YT_LINK_1),
                    Button.url("❤️ 3# YouTube", YT_LINK_2)
                ],
                # Telegram Public Channels နှစ်ခု ဘေးချင်းယှဉ်
                [
                    Button.url("📢 1# Subscribe", f"https://t.me/ttgk776"),
                    Button.url("📢 2# Subscribe", f"https://t.me/ggiik77")
                ],
                # Folder ကို အောက်မှာ အပြည့်ထားမယ်
                [Button.url("📁 Join Folder", FOLDER_LINK)],
                # Done Button
                [Button.inline("✅ Done", b"check_sub")]
            ]
            await event.respond(msg, buttons=sub_btns)
            return False
    return True

async def download_video(event, url, fmt_id):
    path = f"dl_{event.sender_id}.mp4"
    ydl_opts = {
        'format': f'{fmt_id}+bestaudio/best',
        'outtmpl': path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'external_downloader_args': ['-x', '16', '-k', '1M'],
    }
    msg = await event.respond("🚀 **Downloading... Please wait.**")
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).download([url]))
        await event.client.send_file(event.chat_id, path, caption="✅ Success!")
        await msg.delete()
    except Exception as e:
        await event.respond(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(path): os.remove(path)

# --- [5] EVENT HANDLERS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    await event.respond("Choose Language / ဘာသာစကား ရွေးချယ်ပါ -", buttons=btns)

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup(event):
    lang = event.pattern_match.group(1).decode()
    user_lang[event.sender_id] = lang
    await event.edit("🌟 **Main Menu** 🌟", buttons=get_main_buttons(lang))

@client.on(events.CallbackQuery(data=b"down"))
async def down_trigger(event):
    if not await check_force_sub(event): return
    user_state[event.sender_id] = "waiting_link"
    await event.respond("🔗 YouTube သို့မဟုတ် TikTok link ပို့ပေးပါ။")

@client.on(events.NewMessage)
async def handle_input(event):
    uid = event.sender_id
    if event.text.startswith('/'): return
    
    if user_state.get(uid) == "waiting_link":
        url = event.text
        user_usage_count[uid] = user_usage_count.get(uid, 0) + 1
        if "tiktok.com" in url:
            await download_video(event, url, "bestvideo")
        else:
            btns = [
                [Button.inline("🎬 360p ( ⌛ )", f"y_{url}_360"), Button.inline("🎬 480p ( ⌛ )", f"y_{url}_480")],
                [Button.inline("🎬 720p ( ⌛ )", f"y_{url}_720"), Button.inline("🎬 1080p", f"y_{url}_1080")],
                [Button.inline("🎵 Audio", f"y_{url}_bestaudio")]
            ]
            await event.respond("📺 **YouTube Video Found**\nSelect Quality:", buttons=btns)
        user_state[uid] = None

@client.on(events.CallbackQuery(pattern=r"y_(.+)_(.+)"))
async def yt_click(event):
    url = event.pattern_match.group(1).decode()
    q = event.pattern_match.group(2).decode()
    fmt = f"bestvideo[height<={q}]" if q != "bestaudio" else "bestaudio"
    await event.edit("⏳ Processing...")
    await download_video(event, url, fmt)

@client.on(events.CallbackQuery(data=b"check_sub"))
async def verify(event):
    if await is_subscribed(event.sender_id):
        await event.edit("✅ Success!", buttons=get_main_buttons(user_lang.get(event.sender_id, "en")))
    else:
        await event.answer("❌ မJoinရသေးပါဘူးဗျာ။ အကုန် Join ပေးပါ။", alert=True)

print("Bot is starting with Final UI...")
client.run_until_disconnected()
