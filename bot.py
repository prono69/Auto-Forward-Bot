import logging
import asyncio
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, FORWARD_MAP

# Basic config: logs to console with timestamps & levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = Client("forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

media_group_buffer = defaultdict(list)
media_group_tasks = {}

@app.on_message(filters.chat(list(FORWARD_MAP.keys())))
async def forward_handler(client: Client, message: Message):
    src_chat_id = message.chat.id
    dst_chat_id = FORWARD_MAP[src_chat_id]

    # Handle media group (album)
    if message.media_group_id:
        group_id = message.media_group_id
        media_group_buffer[group_id].append(message)

        if group_id not in media_group_tasks:
            media_group_tasks[group_id] = asyncio.create_task(
                send_album_group(client, src_chat_id, dst_chat_id, group_id)
            )

    else:
        # Handle single message or media
        try:
            if message.text or message.caption:
                await message.copy(chat_id=dst_chat_id, caption=message.caption or None)
        except Exception as e:
            logger.error(f"❌ Error forwarding single message: {e}")

async def send_album_group(client: Client, src_chat_id: int, dst_chat_id: int, group_id: str):
    await asyncio.sleep(1.5)  # Wait for album to complete

    messages = media_group_buffer[group_id]
    try:
        await client.copy_media_group(
            chat_id=dst_chat_id,
            from_chat_id=src_chat_id,
            message_id=messages[0].message_id
        )
    except Exception as e:
        logger.error(f"❌ Error forwarding album (group_id={group_id}): {e}")
    finally:
        media_group_buffer.pop(group_id, None)
        media_group_tasks.pop(group_id, None)

if __name__ == "__main__":
    try:
        logger.info("Bot Started!")
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logger.error(err)
    finally:
        logger.info("Bot Stopped")

