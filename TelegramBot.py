from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import json

TOTAL_RANGE = 3100 - 1220
BOT_TOKEN = os.getenv('BOT_TOKEN')
log_file = "log.json"

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_message = f"Welcome to Lou's plant bot."
    if update.effective_chat.type in ['group', 'supergroup']:
        userID = update.effective_chat.id      
    else:
        userID = update.effective_user.id
    if str(userID) not in GetSubscribers():
        start_message += "\n\nYou have been subscribed to receive updates. Use the /stop command to unsubscribe"
        AddSubscribers(userID)
    start_message += "\n\nUse the /plantstatus command to get the current humidity status of the plant"
    await context.bot.send_message(chat_id=userID, text=start_message)
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

def write_list_to_file(file_path:str, items:list):
    """
    Writes a list of items to a file. Each item in the list is written on a new line.
    
    :param file_path: Path to the file to write.
    :param items: List of items to write to the file.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            for item in items:
                file.write(f"{item}\n")
        file.close()
        return True
    except FileNotFoundError:
        with open(file_path, 'a', encoding='utf-8') as file:
            for item in items:
                file.write(f"{item}\n")
        file.close()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def GetSubscribers():
    return read_list_from_file(os.path.curdir + "/subscribers.txt")
def AddSubscribers(new_subscriber):
    subscribers = GetSubscribers()
    subscribers.append(new_subscriber)
    return write_list_to_file(os.path.curdir + "/subscribers.txt", subscribers)
def RemoveSubscribers(subscriber):
    subscribers = GetSubscribers()
    subscribers.remove(str(subscriber))
    return write_list_to_file(os.path.curdir + "/subscribers.txt", subscribers)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        userID = update.effective_chat.id      
    else:
        userID = update.effective_user.id
    if str(userID) in GetSubscribers():
        RemoveSubscribers(userID)
        await context.bot.send_message(chat_id=userID, text="You have been unsubscribed from updates. Use the /start command to subscribe again")

def constrain(value, min_value, max_value):
    return max(min_value, min(value, max_value))

async def plantStatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        userID = update.effective_chat.id
    else:
        userID = update.effective_user.id
    mac_address = update.message.text.replace("@LousPlantHumidityBot","").replace("/plantstatus", "").strip()
    data = json.loads(get_status())
    try:
        message = "📡 *Sensor Data Update* 📡\n\n"
        if len(mac_address) > 0 or len(data.items()) == 1: 
            details = data[mac_address]
            message += f"🔹 *MAC Address:* `{mac_address}`\n"
            if details :
                cappedSoilValue = constrain(float(details['payload']), 0, TOTAL_RANGE)
                humidity_percentage = 100 - (cappedSoilValue / TOTAL_RANGE) * 100
                message += f"💦 *Current Humidity:* {humidity_percentage:.2f}%\n"
                message += f"⏳ *Last update:* {details['timestamp']}\n"
                battery = details['batterylevel'] if details['batterylevel'] else None
                if battery:
                    message += f"🔋 *Battery Level:* {battery}\n"
        else:
            for mac, details in data.items():
                message += f"🔹 *MAC Address:* `{mac}`\n"
                if details :
                    cappedSoilValue = constrain(float(details['payload']), 0, TOTAL_RANGE)
                    humidity_percentage = 100 - (cappedSoilValue / TOTAL_RANGE) * 100
                    message += f"💦 *Current Humidity:* {humidity_percentage:.2f}%\n"
                    message += f"⏳ *Last update:* {details['timestamp']}\n"
                    battery = details['batterylevel'] if details['batterylevel'] else None
                    if battery:
                        message += f"🔋 *Battery Level:* {battery}\n"
                    message += "➖➖➖➖➖➖➖➖➖➖\n"
                else:
                    message += f"🤷‍♂️ No data available\n"
    except Exception as e:
        message = "Invalid Mac Address"
    await context.bot.send_message(chat_id=userID, text=message, parse_mode="Markdown")    
    return
def get_status():
    with open(log_file, 'r') as file:
        log_data = json.load(file)

    # Extract the last message for each MAC address
    status_data = {
        response["MACAddress"]: response["messages"][-1] if response["messages"] else None
        for response in log_data["responses"]
    }

    return json.dumps(status_data, indent=4)

if __name__ == "__main__":
    # Create the application with your bot's token
    telegram_bot_application = Application.builder().token(BOT_TOKEN).build()
    
    # Add a CommandHandler for the /start command
    telegram_bot_application.add_handler(CommandHandler("start", start))
    
    # Add a CommandHandler for the /plantStatus command
    telegram_bot_application.add_handler(CommandHandler("plantstatus", plantStatus))
    
    telegram_bot_application.add_handler(CommandHandler("stop", stop))
    
    telegram_bot_application.run_polling()

