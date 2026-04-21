import os
import asyncio
import edge_tts
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Config ---
API_ID = 32153130
API_HASH = "66168465c6360e3d856a8a53a3d21e84"
BOT_TOKEN = "8578954674:AAEJjE2hQ3fm7ylTxb0s98gauJOVTbwJ0I8" 

app = Client("my_all_in_one_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User Database
user_data = {} 

# --- Strings & Voices ---
STRINGS = {
    "en": {
        "welcome": "Welcome! Send me a Video Link or Text.",
        "choose": "What would you like to do?",
        "wait": "Please wait... Processing... ⏳",
        "dl": "🎬 Downloader", "tr": "📄 Transcript", "set": "🌍 Languages",
        "select_voice": "Choose a Voice:", "done": "Completed! ✅"
    },
    "mm": {
        "welcome": "မင်္ဂလာပါ! ဗီဒီယို Link သို့မဟုတ် စာသား ပို့ပေးပါ။",
        "choose": "ဘာလုပ်ချင်လဲ ရွေးချယ်ပါ-",
        "wait": "ခဏစောင့်ပါ... လုပ်ဆောင်နေပါပြီ... ⏳",
        "dl": "🎬 ဒေါင်းလုဒ်ဆွဲရန်", "tr": "📄 စာသားထုတ်ရန်", "set": "🌍 ဘာသာစကား",
        "select_voice": "အသံရွေးချယ်ပါ-", "done": "ပြီးစီးပါပြီ! ✅"
    }
}

VOICES = {
    "mm": {"name": "🇲🇲 Burmese", "v": [["Thiha (Male)", "my-MM-ThihaNeural"], ["Nilar (Female)", "my-MM-NilarNeural"]]},
    "en": {"name": "🇬🇧 English", "v": [
        ["Ava (F)", "en-US-AvaNeural"], ["Emma (F)", "en-US-EmmaNeural"], ["Ana (F)", "en-US-AnaNeural"],
        ["Andrew (M)", "en-US-AndrewNeural"], ["Brian (M)", "en-GB-BrianNeural"], ["Ryan (M)", "en-GB-RyanNeural"]
    ]},
    "jp": {"name": "🇯🇵 Japanese", "v": [["Nanami (F)", "ja-JP-NanamiNeural"], ["Keita (M)", "ja-JP-KeitaNeural"]]},
    "th": {"name": "🇹🇭 Thai", "v": [["Premwadee (F)", "th-TH-PremwadeeNeural"], ["Niwat (M)", "th-TH-NiwatNeural"]]},
    "es": {"name": "🇪🇸 Spanish", "v": [["Elvira (F)", "es-ES-ElviraNeural"], ["Alvaro (M)", "es-ES-AlvaroNeural"]]}
}

def get_u(uid):
    if uid not in user_data: user_data[uid] = {"lang": "en", "text": ""}
    return user_data[uid]

@app.on_message(filters.command("start"))
async def start(client, message):
    u = get_u(message.from_user.id)
    await message.reply(STRINGS[u["lang"]]["welcome"])

@app.on_message(filters.text & filters.private)
async def handle_msg(client, message):
    uid = message.from_user.id
    u = get_u(uid)
    u["text"] = message.text
    lang = u["lang"]

    if message.text.startswith("http"):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(STRINGS[lang]["dl"], callback_data="dl_video"),
             InlineKeyboardButton(STRINGS[lang]["tr"], callback_data="get_tr")],
            [InlineKeyboardButton(STRINGS[lang]["set"], callback_data="open_lang")]
        ])
        await message.reply(STRINGS[lang]["choose"], reply_markup=kb)
    else:
        btns = []
        row = []
        for code, info in VOICES.items():
            row.append(InlineKeyboardButton(info["name"], callback_data=f"tts_l_{code}"))
            if len(row) == 2: btns.append(row); row = []
        if row: btns.append(row)
        await message.reply("Select Language for TTS:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query()
async def callbacks(client, query):
    uid = query.from_user.id
    u = get_u(uid)
    data = query.data

    if data == "open_lang":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🇲🇲 Myanmar", callback_data="set_mm")], [InlineKeyboardButton("🇬🇧 English", callback_data="set_en")]])
        await query.message.edit_text("Choose Language:", reply_markup=kb)
    
    elif data.startswith("set_"):
        u["lang"] = data.split("_")[1]
        await query.answer("Updated!", show_alert=True)
        await query.message.edit_text(STRINGS[u["lang"]]["welcome"])

    elif data.startswith("tts_l_"):
        l_code = data.split("_")[2]
        btns = []
        row = []
        for v_name, v_id in VOICES[l_code]["v"]:
            row.append(InlineKeyboardButton(v_name, callback_data=f"v_{v_id}"))
            if len(row) == 2: btns.append(row); row = []
        if row: btns.append(row)
        await query.message.edit_text(STRINGS[u["lang"]]["select_voice"], reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("v_"):
        v_id = data.split("_")[1]
        await query.message.edit_text(STRINGS[u["lang"]]["wait"])
        path = f"tts_{uid}.mp3"
        comm = edge_tts.Communicate(u["text"], v_id)
        await comm.save(path)
        await client.send_audio(query.message.chat.id, audio=path, caption=STRINGS[u["lang"]]["done"])
        if os.path.exists(path): os.remove(path)

    elif data == "dl_video":
        await query.message.edit_text(STRINGS[u["lang"]]["wait"])
        try:
            ydl_opts = {'format': 'best', 'outtmpl': f'dl_{uid}.mp4', 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([u["text"]])
            await client.send_video(query.message.chat.id, video=f'dl_{uid}.mp4')
            if os.path.exists(f'dl_{uid}.mp4'): os.remove(f'dl_{uid}.mp4')
        except Exception as e:
            await query.message.reply(f"Error: {str(e)}")

# --- Event Loop Fix for Render ---
async def main():
    async with app:
        print("Bot is running...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except RuntimeError:
        # Loop ပတ်မရတဲ့အခါ Backup အနေနဲ့ သုံးဖို့
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
