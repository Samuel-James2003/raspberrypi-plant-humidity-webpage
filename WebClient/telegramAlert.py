from telegram import Bot
import os
from debug import log_event
def send_update(mac_address, BOT_TOKEN):
    try:
        for chat in GetSubscribers():
            bot = Bot(token=BOT_TOKEN)
            alert_message = f"*Humidity Alert* 🌿\n\n💧The device at *MAC Address:* `{mac_address}` is below 50% soil humidity\nPlease water me soon!"
            bot.send_message(chat_id=chat, text=alert_message, parse_mode="Markdown")
    except Exception as e:
         log_event(f"An error occurred: {e}", level="ERROR", exc_info=True)
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
