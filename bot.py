import os
from io import BytesIO
import logging
import asyncio
import random
from collections import defaultdict, deque
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, STICKER_IDS
from map_utils import load_map, add_mapping

# Basic config: logs to console with timestamps & levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs.txt"),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

# Suppress verbose logs from Pyrogram internals
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)
logging.getLogger("pyrogram.connection.connection").setLevel(logging.WARNING)

app = Client("forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

media_group_buffer = defaultdict(list)
media_group_queue = deque()
processing_album = False
media_group_tasks = {}
FORWARD_MAP = load_map()
MAX_MESSAGE_LENGTH = 4096

# start command 
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    sticker = random.choice(STICKER_IDS)
    try:
        await message.reply_sticker(sticker)
    except Exception:
        await message.reply_video(sticker)

    await message.reply_text(
        "👋 **Hey there!**\n\n"
        "🛰️ Welcome to **Pyrogram Forwarder Bot** — your personal Telegram message relay system!\n\n"
        "📨 **This bot automatically forwards:**\n"
        "  ➜ 📥 __Text messages__\n"
        "  ➜ 🖼️ __Media (photo/video/docs)__\n"
        "  ➜ 🖼️📁 __Full__ **media albums** __as proper Telegram albums__\n\n"
        "📦 **Your chats are mapped from source ➝ target with full caption support.**\n"
        "⚡ **It’s fast, reliable, and Docker-powered.**\n\n"
        "ℹ️ **Use it inside your deployment or fork and customize it for yourself.**\n\n"
        "🧑‍💻 Made with 💙 using [PyroFork](https://pyrofork.wulan17.dev/main/)\n\n"
        "__Ready when you are... just send a message in your source chat!__",
        disable_web_page_preview=True,
        quote=True
    )

# logs command
@app.on_message(filters.command("logs") & filters.user(OWNER_ID))
async def send_logs(client, message):
    try:
        await message.reply_document("logs.txt", caption="🗂️ Log file")
    except Exception as e:
        await message.reply_text(f"❌ Couldn't send logs: `{e}`")
        
        
# setmap command 
@app.on_message(filters.command("setmap") & filters.user(OWNER_ID))
async def setmap_cmd(client, message: Message):
    try:
        response = await message.ask(
            "**🔄 Set a new forward mapping**\n\n"
            "Please send the `source_chat_id` and `target_chat_id`, separated by a space.\n\n"
            "Example:\n`-1001234567890 -1009876543210`",
            timeout=120
        )

        parts = response.text.strip().split()

        if len(parts) != 2:
            return await response.reply("⚠️ Please provide exactly 2 chat IDs separated by space.")

        src_id, tgt_id = int(parts[0]), int(parts[1])

        # Validate both chats
        try:
            src = await client.get_chat(src_id)
            tgt = await client.get_chat(tgt_id)
        except Exception as e:
            return await response.reply(f"❌ Invalid chat ID(s): `{e}`")

        # Save the mapping
        add_mapping(src_id, tgt_id)
        FORWARD_MAP.clear()
        FORWARD_MAP.update(load_map())

        await response.reply(
            f"✅ Mapping saved:\n\n"
            f"**Source:** {src.title or src.username} (`{src_id}`)\n"
            f"**Target:** {tgt.title or tgt.username} (`{tgt_id}`)"
        )

    except asyncio.TimeoutError:
        await message.reply("⏰ Timeout. Please try `/setmap` again.")
       
        
# showmap command
@app.on_message(filters.command("showmap") & filters.user(OWNER_ID))
async def show_map_cmd(client, message: Message):
    mappings = load_map()

    if not mappings:
        return await message.reply("⚠️ No source ➝ target mappings found yet.")

    msg = "**📌 Current Source ➝ Target Mappings:**\n\n"

    for src_id, tgt_id in mappings.items():
        try:
            src_chat = await client.get_chat(int(src_id))
            tgt_chat = await client.get_chat(int(tgt_id))

            src_name = src_chat.title or src_chat.username or f"Chat {src_id}"
            tgt_name = tgt_chat.title or tgt_chat.username or f"Chat {tgt_id}"

            msg += f"• **{src_name}** (`{src_id}`)\n  ➝ **{tgt_name}** (`{tgt_id}`)\n\n"
        except Exception as e:
            msg += f"• `{src_id}` ➝ `{tgt_id}` (⚠️ Error: {e})\n\n"

    await message.reply(msg, disable_web_page_preview=True)
    
    
# bash command
@app.on_message(filters.command("bash") & filters.user(OWNER_ID))
async def execution(client, message):
    status_message = await message.reply_text("`Processing ...`")
    
    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await status_message.edit("No command provided!")
    
    reply_to_ = message.reply_to_message or message
    
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    stderr_output = stderr.decode().strip() or "😂"
    stdout_output = stdout.decode().strip() or "😐"
    
    output = (
        f"<b>QUERY:</b>\n<u>Command:</u>\n<code>{cmd}</code>\n"
        f"<u>PID</u>: <code>{process.pid}</code>\n\n"
        f"<b>stderr</b>: \n<code>{stderr_output}</code>\n\n"
        f"<b>stdout</b>: \n<code>{stdout_output}</code>"
    )
    
    if len(output) > MAX_MESSAGE_LENGTH:
        with BytesIO(output.encode()) as out_file:
            out_file.name = "exec.txt"
            await reply_to_.reply_document(
                document=out_file,
                caption=cmd[: MAX_MESSAGE_LENGTH // 4 - 1],
                disable_notification=True,
                quote=True,
            )
            os.remove("exec.txt")
    else:
        await reply_to_.reply_text(output, quote=True)
    
    await status_message.delete()

# Main forward handler
@app.on_message()
async def forward_handler(client, message: Message):
    src_chat_id = str(message.chat.id)

    if src_chat_id not in FORWARD_MAP:
        return

    if message.text and message.text.startswith(("/", ".")):
        return

    dst_chat_id = FORWARD_MAP[src_chat_id]

    if message.media_group_id:
        group_key = f"{src_chat_id}:{message.media_group_id}"
        media_group_buffer[group_key].append(message)

        # Only queue once
        if group_key not in media_group_queue:
            media_group_queue.append((src_chat_id, dst_chat_id, group_key))
            await process_album_queue(client)

    else:
        try:
            await message.copy(chat_id=dst_chat_id)
        except Exception as e:
            logger.error(f"❌ Error forwarding single message: {e}")



async def process_album_queue(client):
    global processing_album

    if processing_album:
        return  # Already working

    processing_album = True

    while media_group_queue:
        src_chat_id, dst_chat_id, group_key = media_group_queue.popleft()

        await asyncio.sleep(3)  # Buffer album parts

        messages = media_group_buffer[group_key]
        messages = sorted(messages, key=lambda m: m.id)

        try:
            await client.copy_media_group(
                chat_id=dst_chat_id,
                from_chat_id=src_chat_id,
                message_id=messages[0].id
            )
            logger.info(f"📸 Forwarded album with {len(messages)} items")
        except Exception as e:
            logger.error(f"❌ Error forwarding album {group_key}: {e}")
        finally:
            media_group_buffer.pop(group_key, None)

    processing_album = False



async def lol_handle_album_group(client, src_chat_id, dst_chat_id, group_id):
    # await asyncio.sleep(2.5)  # Let Telegram finish sending all parts

    messages = media_group_buffer[group_id]
    # messages = sorted(messages, key=lambda x: x.id)  # Ensure order

    try:
        await client.copy_media_group(
            chat_id=dst_chat_id,
            from_chat_id=src_chat_id,
            message_id=messages[0].id
        )
        logger.info(f"📸 Forwarded album with {len(messages)} items")
    except FloodWait as e:
        logger.warning(f"🌊 FloodWait in album: sleeping {e.value}s")
        await asyncio.sleep(e.value)
        await client.copy_media_group(
            chat_id=dst_chat_id,
            from_chat_id=src_chat_id,
            message_id=messages[0].id
        )
    except Exception as e:
        logger.error(f"❌ Error forwarding album: {e}")
    finally:
        # Cleanup
        media_group_buffer.pop(group_id, None)
        media_group_tasks.pop(group_id, None)


if __name__ == "__main__":
    try:
        logger.info("🎉 Bot Started!")
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logger.error(err)
    finally:
        logger.info("Bot Stopped")

