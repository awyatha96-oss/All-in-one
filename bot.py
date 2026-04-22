import os
import asyncio
import edge_tts
from telethon import TelegramClient, events, Button
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL

# --- [1] CONFIGURATION ---
API_ID = 32153130
API_HASH = '66168465c6360e3d856a8a53a3d21e84'
BOT_TOKEN = '8570099841:AAFBp8z--d3hb2V0wWa54Ir2HgXxU-A47yk'

# Channels & Links
YOUTUBE_URL = "https://www.youtube.com/@VibeFootyTV"
PUBLIC_CHANNELS = ["@ttgk776", "@ggiik77"]
FOLDER_LINK = "https://t.me/addlist/0wjAKED6UWk4MzE1"

# Folder ထဲမှာပါတဲ့ Public Channel (မင်း Bot ကို Admin ခန့်ထားတဲ့တစ်ခု)
# Folder join ထားမထား စစ်ဖို့အတွက် ဒီ Channel ကို သုံးပါမယ်
FOLDER_CHECK_CHANNEL = "@ttgk776" 

client = TelegramClient('all_in_one_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_lang = {}  
user_state = {} 
temp_data = {}  
user_usage_count = {}

# --- [2] STRINGS ---
STRINGS = {
    "en": {
        "intro": "👋 **Welcome!**\nThis is your All-in-One Bot.\n\n📖 **Features:**\n• Video Downloader (YT/TT)\n• YouTube Transcript\n• Global Translation\n• Text to Speech (TTS)\n\nSelect a service below to start!",
        "sub_msg": "⚠️ **Subscription Required!**\nPlease subscribe to our YouTube and Join our Folder to continue using the bot.",
        "wait": "Processing... Please wait."
    },
    "mm": {
        "intro": "👋 **မင်္ဂလာပါ!**\nဒါကတော့ ဝန်ဆောင်မှုစုံလင်စွာပါဝင်တဲ့ All-in-One Bot ဖြစ်ပါတယ်။\n\n📖 **ပါဝင်သော လုပ်ဆောင်ချက်များ:**\n• ဗီဒီယိုဒေါင်းလုဒ် (YouTube/TikTok)\n• YouTube စာသားထုတ်ယူခြင်း\n• ဘာသာစကား ဘာသာပြန်ခြင်း\n• စာသားကို အသံပြောင်းခြင်း (TTS)\n\nစတင်အသုံးပြုရန် အောက်ပါ Menu မှ တစ်ခုကို ရွေးချယ်ပါ!",
        "sub_msg": "⚠️ **Channel Join ရန်လိုအပ်ပါသည်!**\nBot ကို ဆက်လက်အသုံးပြုရန် ကျွန်ုပ်တို့၏ YouTube ကို Subscribe လုပ်ပြီး Folder ကို Join ပေးပါ။",
        "wait": "ခဏစောင့်ပါ... လုပ်ဆောင်နေပါတယ်။"
    }
}

# --- [3] HELPER FUNCTIONS ---
def get_main_buttons(lang):
    return [
        [Button.inline("🌐 Languages", b"lang"), Button.inline("📥 Downloader", b"down")],
        [Button.inline("📝 Transcript", b"script"), Button.inline("🔠 Translation", b"trans")],
        [Button.inline("🗣 Text To Speech", b"tts")]
    ]

async def is_subscribed(user_id):
    try:
        # Public Channels ၂ ခုလုံးမှာ ရှိမရှိ စစ်မယ်
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
            btns = [
                [Button.url("❤️ Subscribe YouTube", YOUTUBE_URL)],
                [Button.url("📁 Join Folder (Private + Public)", FOLDER_LINK)],
                [Button.inline("✅ Done (လုပ်ပြီးပါပြီ)", b"check_sub")]
            ]
            await event.respond(STRINGS[lang]["sub_msg"], buttons=btns)
            return False
    return True

# --- [4] BOT EVENTS ---

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    btns = [[Button.inline("🇲🇲 Myanmar", b"setup_mm")], [Button.inline("🇬🇧 English", b"setup_en")]]
    await event.respond("Select Language / ဘာသာစကား ရွေးချယ်ပါ -", buttons=btns)

@client.on(events.CallbackQuery(pattern=r"setup_(\w+)"))
async def setup_lang(event):
    lang = event.pattern_match.group(1).decode()
    user_lang[event.sender_id] = lang
    await event.edit(STRINGS[lang]["intro"], buttons=get_main_buttons(lang))

@client.on(events.CallbackQuery(data=b"check_sub"))
async def verify_sub(event):
    uid = event.sender_id
    if await is_subscribed(uid):
        lang = user_lang.get(uid, "en")
        await event.edit("✅ Success! You can now use the bot.", buttons=get_main_buttons(lang))
    else:
        await event.answer("❌ You haven't joined all channels yet!", alert=True)

# --- Downloader & Other Services Logic ---
@client.on(events.CallbackQuery(data=b"down"))
async def download_menu(event):
    if not await check_force_sub(event): return
    user_state[event.sender_id] = "waiting_link"
    msg = "Send YouTube or TikTok link:" if user_lang.get(event.sender_id) == "en" else "ဗီဒီယို Link ပို့ပေးပါ။"
    await event.edit(msg)

# (မှတ်ချက်: Video Downloader, TTS နှင့် Translation logic များကို အရင်ပို့ထားသော version အတိုင်း ဤနေရာတွင် ဆက်လက်ပေါင်းစပ်နိုင်ပါသည်)

@client.on(events.NewMessage)
async def global_handler(event):
    uid = event.sender_id
    if event.text.startswith('/'): return
    
    # ပထမတစ်ကြိမ် အလကားသုံးပြီးနောက် အသုံးပြုမှုမှတ်တမ်းတိုးရန်
    if uid not in user_usage_count:
        user_usage_count[uid] = 0
    
    # လက်ရှိ လုပ်ဆောင်နေသော state အလိုက် logic များ (Downloader, TTS, etc.)
    # ... (ယခင် code များအတိုင်း) ...

print("Bot credentials loaded. Running now...")
client.run_until_disconnected()
