from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import json


BOT_TOKEN = os.getenv('BOT_TOKEN')
log_file = "log.json"
# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"Hello, {user.first_name}! Welcome to Lou's plant bot. 😊\nUse the command /plantstatus to see the plant humidity add [Mac Address] to see a specific humidity"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

async def plantStatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        userID = update.effective_chat.id
    else:
        userID = update.effective_user.id
    mac_address = update.message.text.replace("/plantstatus", "").strip()
    data = json.loads(get_status())
    try:
        message = "📡 *Sensor Data Update* 📡\n\n"
        if len(mac_address) > 0: 
            details = data[mac_address]
            message += f"🔹 *MAC Address:* `{mac_address}`\n"
            if details :
                humidity_percentage = 100 - (float(details['payload']) / 1680) * 100
                message += f"💦 *Current Humidity:* {humidity_percentage:.2f}%\n"
                message += f"⏳ *Last update:* {details['timestamp']}\n"
                battery = details['batterylevel'] if details['batterylevel'] else None
                if battery:
                    message += f"🔋 *Battery Level:* {battery}\n"
        else:
            for mac, details in data.items():
                message += f"🔹 *MAC Address:* `{mac}`\n"
                if details :
                    humidity_percentage = 100 - (float(details['payload']) / 1680) * 100
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
    
    telegram_bot_application.run_polling()
