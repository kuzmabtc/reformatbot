import logging
import re
from aiogram import Bot, Dispatcher, types

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace 'YOUR_BOT_TOKEN' with your Telegram Bot token
API_TOKEN = '7154336105:AAFbnSkhTovHy8mOlySkb0WmNKons6Dnd2w'
CHANNEL_ID = '-1002013637466'  # Replace with your Telegram channel ID

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Function to parse signal message and extract details
def parse_signal_message(message_text):
    # Initialize variables to store extracted details
    direction = None
    trading_pair = None
    entry_prices = []
    take_profit_targets = []
    stop_loss = None
    leverage = None
    funds_percentage = None

    # Split the message into lines and process each line
    lines = message_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Determine section based on keywords
        if 'long' in line.lower() or 'short' in line.lower():
            direction = line.upper()
        elif '/' in line:
            trading_pair = line
        elif line.startswith('Entry'):
            current_section = 'entry'
        elif line.startswith('Take-Profit Targets'):
            current_section = 'take_profit'
        elif line.startswith('Stop Loss'):
            stop_loss_match = re.match(r'^Stop Loss:\s*-\s*([\d.]+)', line)
            if stop_loss_match:
                stop_loss = stop_loss_match.group(1)
        elif line.startswith('Use'):
            use_match = re.match(r'Use (\d+)X Leverage and (\d+)% Funds', line)
            if use_match:
                leverage = use_match.group(1)
                funds_percentage = use_match.group(2)
        elif line.startswith('Trailing Configuration'):
            current_section = None

        # Process current section
        if current_section == 'entry':
            entry_match = re.match(r'^\d+\)\s*([\d.]+)', line)
            if entry_match:
                entry_prices.append(entry_match.group(1))
        elif current_section == 'take_profit':
            target_match = re.match(r'^\d+\)\s*([\d.]+)\s*-\s*\d+%', line)
            if target_match:
                take_profit_targets.append(target_match.group(1))

    # Check if essential details are missing
    if not entry_prices or not take_profit_targets or not leverage or not funds_percentage:
        return None

    return {
        'direction': direction,
        'trading_pair': trading_pair,
        'entry_prices': entry_prices,
        'take_profit_targets': take_profit_targets,
        'stop_loss': stop_loss,
        'leverage': leverage,
        'funds_percentage': funds_percentage
    }

# Function to format the parsed signal details into the desired output message
def format_signal_message(parsed_details):
    if not parsed_details:
        return None

    # Extract relevant details
    direction = parsed_details['direction']
    trading_pair = parsed_details['trading_pair']
    entry_prices = parsed_details['entry_prices']
    take_profit_targets = parsed_details['take_profit_targets']
    stop_loss = parsed_details['stop_loss']
    leverage = parsed_details['leverage']
    funds_percentage = parsed_details['funds_percentage']

    # Prepare the formatted message
    formatted_message = (
        f"Future Trade\n\n"
        f"{direction}\n\n"
        f"{trading_pair}\n\n"
    )

    if entry_prices:
        formatted_message += "Entry\n"
        formatted_message += '\n'.join(f"{i}) {price}" for i, price in enumerate(entry_prices, start=1)) + "\n\n"

    if take_profit_targets:
        formatted_message += "Take-Profit Targets:\n"
        formatted_message += '\n'.join(f"{i}) {target}" for i, target in enumerate(take_profit_targets, start=1)) + "\n\n"

    if stop_loss:
        formatted_message += f"Stop Loss: {stop_loss}\n\n"

    if leverage and funds_percentage:
        formatted_message += f"Use {leverage}X Leverage and {funds_percentage}% Funds\n"

    return formatted_message

# Registering a handler for text messages
@dp.message_handler(content_types=types.ContentType.TEXT)
async def reformat_signal(message: types.Message):
    # Parse the signal message
    signal_details = parse_signal_message(message.text)

    # Format the parsed details into the desired output message
    formatted_message = format_signal_message(signal_details)

    # Send the reformatted message back to the user if it's valid
    if formatted_message:
        await message.reply(formatted_message)

        # Send the message to your Telegram channel
        await bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)

# Start the bot
if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(dp.start_polling())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        loop.close()
