import os
import asyncio
import threading
import http.server
import socketserver
from telethon import TelegramClient, events, Button
from yt_dlp import YoutubeDL

# --- [1] RENDER PORT BINDING FIX ---
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

YT_LINK_1 = "https://www.youtube.com/@VibeFootyTV"
YT_LINK_2 = "http://googleusercontent.com/youtube.com/another_yt"
FOLDER_LINK = "https://t.me/addlist/0wjAKED6UWk4MzE1"
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}
user_state = {}
user_usage_count = {}
last_msg_ids = {} # စာဟောင်းများ ပြန်ဖျက်ရန် ID သိမ်းဆည်းသည့်နေရာ

# --- [3] UI MENUS ---
def get_main_buttons(lang):
    return [
        [Button.inline("📥 Video Downloader", b"down")],
        [Button.inline("🗣 Text To Speech", b"tts"), Button.inline("🔠 Translation", b"trans")],
        [Button.inline("📝 YouTube Transcript", b"script"), Button.inline("🌐 Languages", b"lang")],
        [Button.inline("📩 Contact Admin", b"contact"), Button.inline("❓ Help", b"help")]
    ]

async def is_subscribed(user_id):
    try:
        for ch in PUBLIC_CHANNELS:
            p = await client.get_permissions(ch, user_id)
            if not p: return False
        return True
    except:
        return False

# စာဟောင်းများ ဖျက်ပေးမည့် Helper Function
async def cleanup(chat_id, user_id):
    if user_id in last_msg_ids:
        try:
            await client.delete_messages(chat_id, last_msg_ids[user_id])
            del last_msg_ids[user_id]
        except: pass

# --- [4] EVENT HANDLERS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    await cleanup(event.chat_id, uid) # အရင်ရှိနေတဲ့ စာဟောင်းဖျက်မယ်
    
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    sent = await event.respond("Choose Language / ဘာသာစကား ရွေးချယ်ပါ -", buttons=btns)
    last_msg_ids[uid] = sent.id

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup_lang(event):
    uid = event.sender_id
    lang = event.pattern_match.group(1).decode()
    user_lang[uid] = lang
    
    # ဘာသာစကားရွေးပြီးရင် အရင်စာကိုဖျက်မယ်
    await cleanup(event.chat_id, uid)
    
    sent = await event.respond("🌟 **Main Menu** 🌟", buttons=get_main_buttons(lang))
    last_msg_ids[uid] = sent.id

@client.on(events.CallbackQuery(data=b"down"))
async def down_trigger(event):
    uid = event.sender_id
    # Feature တစ်ခုခုနှိပ်လိုက်တာနဲ့ အရင် Intro/Menu စာကိုဖျက်မယ်
    await cleanup(event.chat_id, uid)
    
    # Force Sub Check
    if user_usage_count.get(uid, 0) >= 1 and not await is_subscribed(uid):
        btns = [
            [Button.url("❤️ 1# YouTube", YT_LINK_1), Button.url("❤️ 3# YouTube", YT_LINK_2)],
            [Button.url("📢 1# Subscribe", "https://t.me/ttgk776"), Button.url("📢 2# Subscribe", "https://t.me/ggiik77")],
            [Button.url("📁 Join Folder", FOLDER_LINK)],
            [Button.inline("✅ Done", b"check_sub")]
        ]
        sent = await event.respond("⚠️ **Please join all channels to continue.**", buttons=btns)
        last_msg_ids[uid] = sent.id
        return

    user_state[uid] = "waiting_link"
    sent = await event.respond("🔗 Send Video Link (YouTube/TikTok):")
    last_msg_ids[uid] = sent.id

@client.on(events.CallbackQuery(data=b"check_sub"))
async def verify(event):
    uid = event.sender_id
    if await is_subscribed(uid):
        await cleanup(event.chat_id, uid) # Join ပြီးရင် Join ခိုင်းတဲ့စာကိုဖျက်မယ်
        sent = await event.respond("✅ Success!", buttons=get_main_buttons(user_lang.get(uid, "en")))
        last_msg_ids[uid] = sent.id
    else:
        await event.answer("❌ Please join all channels!", alert=True)

# --- [5] HIGH-SPEED DOWNLOADER ---
async def download_video(event, url, fmt_id):
    path = f"dl_{event.sender_id}.mp4"
    ydl_opts = {
        'format': f'{fmt_id}+bestaudio/best',
        'outtmpl': path,
        'quiet': True,
        'merge_output_format': 'mp4',
        'external_downloader_args': ['-x', '16', '-k', '1M'], # Speed မြန်အောင်လုပ်ထားသည်
    }
    progress = await event.respond("🚀 **Downloading...**")
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).download([url]))
        await event.client.send_file(event.chat_id, path, caption="✅ Complete!")
    except Exception as e:
        await event.respond(f"❌ Error: {str(e)}")
    finally:
        await progress.delete()
        if os.path.exists(path): os.remove(path)

@client.on(events.NewMessage)
async def handle_input(event):
    uid = event.sender_id
    if event.text.startswith('/') or user_state.get(uid) != "waiting_link": return
    
    url = event.text
    user_usage_count[uid] = user_usage_count.get(uid, 0) + 1
    
    await cleanup(event.chat_id, uid) # Link ပို့လိုက်တာနဲ့ အရင်စာကိုဖျက်မယ်

    if "tiktok.com" in url:
        await download_video(event, url, "bestvideo")
    else:
        btns = [
            [Button.inline("🎬 360p ( ⌛ )", f"y_{url}_360"), Button.inline("🎬 480p ( ⌛ )", f"y_{url}_480")],
            [Button.inline("🎬 720p ( ⌛ )", f"y_{url}_720"), Button.inline("🎬 1080p", f"y_{url}_1080")],
            [Button.inline("🎵 Audio", f"y_{url}_bestaudio")]
        ]
        sent = await event.respond("📺 **YouTube Quality Selection**", buttons=btns)
        last_msg_ids[uid] = sent.id
    user_state[uid] = None

@client.on(events.CallbackQuery(pattern=r"y_(.+)_(.+)"))
async def yt_dl(event):
    uid = event.sender_id
    url, q = event.pattern_match.group(1).decode(), event.pattern_match.group(2).decode()
    await cleanup(event.chat_id, uid) # Quality ရွေးပြီးရင် Menu ကိုဖျက်မယ်
    fmt = f"bestvideo[height<={q}]" if q != "bestaudio" else "bestaudio"
    await download_video(event, url, fmt)

print("Bot is active with Auto-Cleanup logic...")
client.run_until_disconnected()
