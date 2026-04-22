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

# --- [1] RENDER PORT BINDING FIX (Web Service Error ရှင်းရန်) ---
def run_dummy_server():
    # Render က ပေးတဲ့ Port ကို မဖြစ်မနေ နားထောင်ပေးရပါမယ်
    port = int(os.environ.get("PORT", 10000)) 
    handler = http.server.SimpleHTTPRequestHandler
    # Port ဖွင့်ပေးထားခြင်းဖြင့် "Port scan timeout" မဖြစ်တော့ပါ
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- [2] CONFIGURATION ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

YT_LINK_1 = "https://www.youtube.com/@VibeFootyTV"
YT_LINK_2 = "youtube.com"
FOLDER_LINK = "https://t.me/addlist/0wjAKED6UWk4MzE1"
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}
user_state = {}
last_msg_ids = {}

# --- [3] REPLY KEYBOARD (စာရိုက်သည့်နေရာမှ ခလုတ်များ) ---
def get_reply_keyboard(lang):
    # မင်းပြထားတဲ့ Icon လေးတွေနဲ့ အညီအညာစီထားပါတယ်
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

# --- [4] HELPER FUNCTIONS ---
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

# --- [5] MAIN HANDLERS ---

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
    # Reply Keyboard Menu ကို ပို့ပေးမည်
    sent = await event.respond(
        "🌟 **Main Menu Activated!**\nခလုတ်များကို စာရိုက်သည့်နေရာတွင် အသုံးပြုနိုင်ပါပြီ။",
        buttons=get_reply_keyboard(lang)
    )
    last_msg_ids[uid] = sent.id

@client.on(events.NewMessage)
async def handle_all_input(event):
    uid = event.sender_id
    text = event.text
    if text.startswith('/'): return

    # --- Menu Button Clicks ---
    if "Video Downloader" in text:
        await cleanup(event.chat_id, uid)
        if not await is_subscribed(uid):
            sub_btns = [
                [Button.url("❤️ YT 1", YT_LINK_1), Button.url("❤️ YT 2", YT_LINK_2)],
                [Button.url("📢 Sub 1", "https://t.me/ttgk776"), Button.url("📢 Sub 2", "https://t.me/ggiik77")],
                [Button.url("📁 Folder", FOLDER_LINK)], [Button.inline("✅ Done", b"check_sub")]
            ]
            sent = await event.respond("⚠️ Please join our channels to continue.", buttons=sub_btns)
            last_msg_ids[uid] = sent.id
            return
        user_state[uid] = "waiting_link"
        sent = await event.respond("🔗 YouTube/TikTok Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "Transcript" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_script"
        sent = await event.respond("📝 YouTube Video Link ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "TTS" in text or "Text To Speech" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_tts"
        sent = await event.respond("🗣 အသံပြောင်းမည့် စာသားကို ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    elif "Translation" in text:
        await cleanup(event.chat_id, uid)
        user_state[uid] = "waiting_trans"
        sent = await event.respond("🔠 ဘာသာပြန်မည့် စာသားကို ပို့ပေးပါ။")
        last_msg_ids[uid] = sent.id

    # --- Feature Processing ---
    elif uid in user_state:
        state = user_state[uid]
        await cleanup(event.chat_id, uid)
        
        if state == "waiting_link":
            btns = [[Button.inline("🎬 720p", f"y_{text}_720"), Button.inline("🎬 1080p", f"y_{text}_1080")],
                    [Button.inline("🎵 Audio", f"y_{text}_audio")]]
            sent = await event.respond("📺 Select Quality:", buttons=btns)
            last_msg_ids[uid] = sent.id
            
        elif state == "waiting_script":
            try:
                vid_id = text.split("v=")[1].split("&")[0] if "v=" in text else text.split("/")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(vid_id)
                full_text = " ".join([i['text'] for i in transcript])
                await event.respond(f"📝 **Transcript:**\n\n{full_text[:3000]}")
            except: await event.respond("❌ Transcript မရနိုင်ပါ (စာတန်းမပါတာ ဖြစ်နိုင်ပါတယ်)")
            
        elif state == "waiting_tts":
            path = f"tts_{uid}.mp3"
            communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
            await communicate.save(path)
            await event.client.send_file(event.chat_id, path, caption="✅ TTS Done!")
            os.remove(path)

        elif state == "waiting_trans":
            res = GoogleTranslator(source='auto', target='my').translate(text)
            await event.respond(f"📝 **ဘာသာပြန်ချက်:**\n\n{res}")
            
        user_state[uid] = None

@client.on(events.CallbackQuery(data=b"check_sub"))
async def verify(event):
    uid = event.sender_id
    if await is_subscribed(uid):
        await cleanup(event.chat_id, uid)
        await event.respond("✅ Verified!", buttons=get_reply_keyboard(user_lang.get(uid, "mm")))
    else:
        await event.answer("❌ အကုန် Join ရပါဦးမယ်!", alert=True)

client.run_until_disconnected()
