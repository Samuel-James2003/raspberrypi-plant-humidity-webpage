from telegram import Bot
import os
import asyncio
import asyncio
from telegram import Bot, ParseMode

async def send_update_async(mac_address, BOT_TOKEN):
    for chat in GetSubscribers():
        bot = Bot(token=BOT_TOKEN)
        alert_message = (
            f"*Humidity Alert* 🌿\n\n"
            f"💧The device at *MAC Address:* `{mac_address}` is below 50% soil humidity\n"
            "Please water me soon!"
        )
        # Await the coroutine returned by send_message
        message = await bot.send_message(chat_id=chat, text=alert_message,  parse_mode="Markdown")
        # Optionally, do something with 'message'
        print(f"Message sent to chat {chat}: {message}")

def send_update(mac_address, BOT_TOKEN):
    # Run the asynchronous helper function
    asyncio.run(send_update_async(mac_address, BOT_TOKEN))
def GetSubscribers():
    return read_list_from_file("./subscribers.txt")
def read_list_from_file(file_path: str):
    """
    Reads a list of items from a file. Each line in the file is treated as one item in the list.
    
    :param file_path: Path to the file to read.
    :return: A list of items read from the file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Strip whitespace/newlines and return as a list
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        # If the file doesn't exist, create it and return an empty list
        with open(file_path, 'a', encoding='utf-8') as file:
            pass
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
