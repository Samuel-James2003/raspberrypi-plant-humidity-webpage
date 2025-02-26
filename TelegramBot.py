from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import json
from WebClient.debug import log_event

TOTAL_RANGE = 3100 - 1220
BOT_TOKEN = os.getenv('BOT_TOKEN')
log_file = "log.json"

####################################################################################################
# Utility functions
####################################################################################################

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
    """
    Retrieve the list of subscribers from the subscribers.txt file.
    
    :return: A list of subscribers."""
    return read_list_from_file(os.path.curdir + "/subscribers.txt")
def AddSubscribers(new_subscriber):
    """
    Add a new subscriber to the list of subscribers.
    
    :param new_subscriber: The subscriber to be added.
    :return: True if the subscriber was added, False otherwise."""
    subscribers = GetSubscribers()
    subscribers.append(new_subscriber)
    return write_list_to_file(os.path.curdir + "/subscribers.txt", subscribers)
def RemoveSubscribers(subscriber):
    """
    Remove a subscriber from the list of subscribers.
    
    :param subscriber: The subscriber to be removed.
    :return: True if the subscriber was removed, False otherwise.
    """
    subscribers = GetSubscribers()
    subscribers.remove(str(subscriber))
    return write_list_to_file(os.path.curdir + "/subscribers.txt", subscribers)
def constrain(value, min_value, max_value):
    """
    Constrains a value within a specified range.

    :param value: The value to be constrained.
    :param min_value: The minimum allowed value.
    :param max_value: The maximum allowed value.

    :return: The constrained value, which will be between min_value and max_value, inclusive.
    """
    return max(min_value, min(value, max_value))
def get_status():
    """
    Retrieves the latest status data from the log file and returns it in JSON format.

    The function reads the log file, extracts the last message for each MAC address,
    and constructs a dictionary with the MAC addresses as keys and the corresponding
    last messages as values. The dictionary is then converted to a JSON string with
    indentation for readability.

    Returns:
    str: A JSON string representing the latest status data for each MAC address.
    """
    with open(log_file, 'r') as file:
        log_data = json.load(file)

    # Extract the last message for each MAC address
    status_data = {
        response["MACAddress"]: response["messages"][-1] if response["messages"] else None
        for response in log_data["responses"]
    }

    return json.dumps(status_data, indent=4)


####################################################################################################
# Handlers for the telegram bot
####################################################################################################

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add the user to the subscribers list, and send a message to the user.
    
    :param update: The Update object containing the information about the Telegram message.
    :param context: The Context object containing the information about the current Telegram session.
    """
    try: 
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
    except Exception as e:
         log_event(f"An error occurred: {e}", level="ERROR", exc_info=True)
        

# Function to handle the /stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove the user from the subscribers list, and send a message to the user.
    
    :param update: The Update object containing the information about the Telegram message.
    :param context: The Context object containing the information about the current Telegram session.
    """
    try:
        if update.effective_chat.type in ['group', 'supergroup']:
            userID = update.effective_chat.id      
        else:
            userID = update.effective_user.id
        if str(userID) in GetSubscribers():
            RemoveSubscribers(userID)
            await context.bot.send_message(chat_id=userID, text="You have been unsubscribed from updates. Use the /start command to subscribe again")
        else:
            await context.bot.send_message(chat_id=userID, text="You are not subscribed to updates.")
    except Exception as e:
         log_event(f"An error occurred: {e}", level="ERROR", exc_info=True)
# Function to handle the /plantstatus command
async def plantStatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get the current humidity status of the plant from the API, and send it as a Telegram message.
    
    :param update: The Update object containing the information about the Telegram message.
    :param context: The Context object containing the information about the current Telegram session.
    """
    try:
        if update.effective_chat.type in ['group', 'supergroup']:
            userID = update.effective_chat.id
        else:
            userID = update.effective_user.id
        mac_address = update.message.text.replace("@LousPlantHumidityBot","").replace("/plantstatus", "").strip()
        data = json.loads(get_status())
        try:
            message = "📡 *Sensor Data Update* 📡\n\n"
            if len(mac_address) > 0: 
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
                        if mac != list(data.keys())[-1]:
                            message += "➖➖➖➖➖➖➖➖➖➖\n"
                    else:
                        message += f"🤷‍♂️ No data available\n"
        except Exception as e:
            message = "Invalid Mac Address"
        await context.bot.send_message(chat_id=userID, text=message, parse_mode="Markdown")    
        return
    except Exception as e:
            log_event(f"An error occurred: {e}", level="ERROR", exc_info=True)

if __name__ == "__main__":
    # Create the application with your bot's token
    telegram_bot_application = Application.builder().token(BOT_TOKEN).build()
    
    # Add a CommandHandler for the /start command
    telegram_bot_application.add_handler(CommandHandler("start", start))
    
    # Add a CommandHandler for the /plantStatus command
    telegram_bot_application.add_handler(CommandHandler("plantstatus", plantStatus))
    
    telegram_bot_application.add_handler(CommandHandler("stop", stop))
    
    telegram_bot_application.run_polling()

