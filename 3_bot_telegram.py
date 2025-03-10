import telebot
from telebot import types
import requests
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
from datetime import datetime, timedelta
from currency_converter import CurrencyConverter
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API key and Bot token from .env
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize currency converter
currency_converter = CurrencyConverter()

# User data storage - more efficient than global variables
user_data = {}

# Common currency pairs for quick access
COMMON_PAIRS = ['USD/EUR', 'EUR/USD', 'USD/GBP', 'GBP/USD', 'GBP/EUR', 'EUR/GBP', 'USD/JPY', 'EUR/JPY']

# Helper functions
def create_currency_keyboard(row_width=2):
    """Create an inline keyboard with common currency pairs."""
    markup = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = [types.InlineKeyboardButton(pair, callback_data=f"convert_{pair.lower()}") for pair in COMMON_PAIRS]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton('Custom pair', callback_data='custom_pair'))
    markup.add(types.InlineKeyboardButton('View exchange rate graph', callback_data='show_graph_options'))
    return markup

def get_exchange_rate(base_currency, target_currency):
    """Get current exchange rate from FastForex API."""
    url = f'https://api.fastforex.io/fetch-one?from={base_currency}&to={target_currency}&api_key={API_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        
        if 'result' in data:
            return data['result'][target_currency]
        else:
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise Exception(f"Connection error: {str(e)}")

def get_historical_rates(base_currency, target_currency, start_date, end_date):
    """Get historical exchange rates from FastForex API."""
    url = f'https://api.fastforex.io/time-series?from={base_currency}&to={target_currency}&start={start_date}&end={end_date}&api_key={API_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data:
            return data['results']
        else:
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise Exception(f"Connection error: {str(e)}")

def create_currency_graph(base, target, days=7):
    """Create a graph of exchange rates for the specified period."""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    try:
        data = get_historical_rates(base, target, start_date, end_date)
        
        # Sort dates to ensure chronological order
        dates = sorted(data.keys())
        rates = [data[date][target] for date in dates]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, rates, marker='o', linestyle='-', color='#3498db', linewidth=2, markersize=8)
        plt.title(f'{base} to {target} Exchange Rate', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel(f'1 {base} = X {target}', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Add current value label
        if dates and rates:
            plt.annotate(f'Current: {rates[-1]:.4f}', 
                        xy=(dates[-1], rates[-1]),
                        xytext=(10, 15),
                        textcoords='offset points',
                        arrowprops=dict(arrowstyle='->', color='red'),
                        color='black',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7))
        
        # Save graph to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    except Exception as e:
        logger.error(f"Graph creation error: {e}")
        raise Exception(f"Failed to create graph: {str(e)}")

# Command handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command."""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"👋 Hello, {user_name}! Welcome to the Currency Converter Bot.\n\n"
        f"This bot can help you convert currencies and view exchange rate trends.\n\n"
        f"Available commands:\n"
        f"• /convert - Start currency conversion\n"
        f"• /graph - View exchange rate graphs\n"
        f"• /help - Show available commands\n"
        f"• /info - About this bot\n\n"
        f"Let's get started! Use /convert to convert currencies."
    )
    
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle /help command."""
    help_text = (
        "📚 *Currency Converter Bot Help*\n\n"
        "*Available Commands:*\n"
        "• /start - Start the bot\n"
        "• /convert - Convert between currencies\n"
        "• /graph - View exchange rate graphs\n"
        "• /help - Show this help message\n"
        "• /info - Information about the bot\n\n"
        
        "*How to Convert Currencies:*\n"
        "1. Use /convert command\n"
        "2. Enter the amount\n"
        "3. Select currency pair or enter custom pair\n\n"
        
        "*How to View Graphs:*\n"
        "1. Use /graph command\n"
        "2. Enter currency pair (e.g., USD/EUR)\n"
        "3. Select time period\n\n"
        
        "*Custom Currency Format:*\n"
        "When entering custom currency pairs, use the format: USD/EUR"
    )
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def info_command(message):
    """Handle /info command."""
    info_text = (
        "ℹ️ *Currency Converter Bot Info*\n\n"
        "This bot allows you to convert between different currencies and view exchange rate graphs.\n\n"
        
        "*Features:*\n"
        "• Real-time currency conversion\n"
        "• Historical exchange rate graphs\n"
        "• Support for multiple currency pairs\n"
        "• Custom currency pair input\n\n"
        
        "*Data Source:*\n"
        "Exchange rates are provided by FastForex API with real-time market data.\n\n"
        
        "*Supported Currencies:*\n"
        "USD, EUR, GBP, JPY, and many more.\n\n"
        
        "Created with ❤️ by Alikhan"
    )
    
    bot.send_message(message.chat.id, info_text, parse_mode='Markdown')

@bot.message_handler(commands=['convert'])
def convert_command(message):
    """Handle /convert command."""
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Enter the amount you want to convert:")
    bot.register_next_step_handler(message, process_amount)

@bot.message_handler(commands=['graph'])
def graph_command(message):
    """Handle /graph command."""
    bot.send_message(
        message.chat.id, 
        "Choose a currency pair for the graph:",
        reply_markup=create_graph_keyboard()
    )

def create_graph_keyboard():
    """Create keyboard for graph currency selection."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(pair, callback_data=f"graph_{pair.lower()}") for pair in COMMON_PAIRS]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton('Custom pair', callback_data='custom_graph_pair'))
    return markup

def create_timeframe_keyboard(pair):
    """Create keyboard for graph timeframe selection."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    options = [
        ('7 days', f"timeframe_{pair}_7"),
        ('14 days', f"timeframe_{pair}_14"),
        ('30 days', f"timeframe_{pair}_30"),
        ('90 days', f"timeframe_{pair}_90")
    ]
    buttons = [types.InlineKeyboardButton(text, callback_data=data) for text, data in options]
    markup.add(*buttons)
    return markup

# Step handlers
def process_amount(message):
    """Process the amount entered by the user."""
    user_id = message.from_user.id
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Store the amount in user data
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['amount'] = amount
        
        # Show currency options
        bot.send_message(
            message.chat.id,
            f"Converting {amount:.2f}. Choose a currency pair:",
            reply_markup=create_currency_keyboard()
        )
    except ValueError:
        bot.send_message(
            message.chat.id, 
            "⚠️ Please enter a valid positive number. Try again:"
        )
        bot.register_next_step_handler(message, process_amount)

def process_custom_pair(message):
    """Process custom currency pair entered by the user."""
    user_id = message.from_user.id
    try:
        # Validate format
        pair = message.text.strip().upper()
        currencies = pair.split('/')
        
        if len(currencies) != 2 or not all(len(c) == 3 for c in currencies):
            raise ValueError("Invalid format")
        
        base, target = currencies
        
        # Get the conversion
        amount = user_data.get(user_id, {}).get('amount', 0)
        try:
            rate = currency_converter.convert(1, base, target)
            result = amount * rate
            
            bot.send_message(
                message.chat.id,
                f"💱 *Conversion Result:*\n\n"
                f"{amount:.2f} {base} = {result:.2f} {target}\n"
                f"Rate: 1 {base} = {rate:.4f} {target}\n\n"
                f"Use /convert to convert another amount.",
                parse_mode='Markdown'
            )
        except Exception as e:
            # Try with FastForex API if CurrencyConverter fails
            try:
                rate = get_exchange_rate(base, target)
                result = amount * rate
                
                bot.send_message(
                    message.chat.id,
                    f"💱 *Conversion Result:*\n\n"
                    f"{amount:.2f} {base} = {result:.2f} {target}\n"
                    f"Rate: 1 {base} = {rate:.4f} {target}\n\n"
                    f"Use /convert to convert another amount.",
                    parse_mode='Markdown'
                )
            except Exception as api_e:
                raise Exception(f"Currency conversion failed: {str(api_e)}")
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "⚠️ Invalid format. Please use the format: USD/EUR"
        )
        bot.register_next_step_handler(message, process_custom_pair)
    
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nPlease try a different currency pair."
        )
        bot.send_message(
            message.chat.id,
            "Enter a currency pair (e.g., USD/EUR):"
        )
        bot.register_next_step_handler(message, process_custom_pair)

def process_custom_graph_pair(message):
    """Process custom currency pair for graph."""
    try:
        # Validate format
        pair = message.text.strip().upper()
        currencies = pair.split('/')
        
        if len(currencies) != 2 or not all(len(c) == 3 for c in currencies):
            raise ValueError("Invalid format")
        
        base, target = currencies
        
        # Store the pair and show timeframe options
        user_id = message.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        
        user_data[user_id]['graph_pair'] = pair
        
        # Show timeframe options
        bot.send_message(
            message.chat.id,
            f"Select time period for {base}/{target} graph:",
            reply_markup=create_timeframe_keyboard(pair.lower())
        )
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "⚠️ Invalid format. Please use the format: USD/EUR"
        )
        bot.register_next_step_handler(message, process_custom_graph_pair)
    
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nPlease try a different currency pair."
        )
        bot.send_message(
            message.chat.id,
            "Enter a currency pair (e.g., USD/EUR):"
        )
        bot.register_next_step_handler(message, process_custom_graph_pair)

# Callback query handlers
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Handle all callback queries."""
    user_id = call.from_user.id
    
    try:
        # Convert currency callbacks
        if call.data.startswith('convert_'):
            pair = call.data.replace('convert_', '')
            base, target = pair.upper().split('/')
            amount = user_data.get(user_id, {}).get('amount', 0)
            
            try:
                rate = currency_converter.convert(1, base, target)
                result = amount * rate
            except Exception:
                # Fallback to API
                rate = get_exchange_rate(base, target)
                result = amount * rate
            
            bot.send_message(
                call.message.chat.id,
                f"💱 *Conversion Result:*\n\n"
                f"{amount:.2f} {base} = {result:.2f} {target}\n"
                f"Rate: 1 {base} = {rate:.4f} {target}\n\n"
                f"Use /convert to convert another amount.",
                parse_mode='Markdown'
            )
        
        # Custom pair callback
        elif call.data == 'custom_pair':
            bot.send_message(
                call.message.chat.id,
                "Enter a currency pair (e.g., USD/EUR):"
            )
            bot.register_next_step_handler(call.message, process_custom_pair)
        
        # Graph callbacks
        elif call.data.startswith('graph_'):
            pair = call.data.replace('graph_', '')
            # Store the pair for later use
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]['graph_pair'] = pair.upper()
            
            # Show timeframe options
            bot.send_message(
                call.message.chat.id,
                f"Select time period for {pair.upper()} graph:",
                reply_markup=create_timeframe_keyboard(pair)
            )
        
        # Custom graph pair callback
        elif call.data == 'custom_graph_pair':
            bot.send_message(
                call.message.chat.id,
                "Enter a currency pair for the graph (e.g., USD/EUR):"
            )
            bot.register_next_step_handler(call.message, process_custom_graph_pair)
        
        # Timeframe callbacks
        elif call.data.startswith('timeframe_'):
            # Extract pair and days
            _, pair, days = call.data.split('_')
            days = int(days)
            
            if user_id in user_data and 'graph_pair' in user_data[user_id]:
                pair = user_data[user_id]['graph_pair']
            
            base, target = pair.upper().split('/')
            
            # Send "generating" message
            processing_msg = bot.send_message(
                call.message.chat.id,
                f"📊 Generating {days}-day graph for {base}/{target}...\n"
                f"This may take a moment."
            )
            
            try:
                # Create and send graph
                graph_buffer = create_currency_graph(base, target, days)
                
                bot.send_photo(
                    call.message.chat.id,
                    graph_buffer,
                    caption=f"📈 {base}/{target} exchange rate over the past {days} days.\n"
                            f"Use /graph to view a different graph."
                )
                
                # Delete processing message
                bot.delete_message(call.message.chat.id, processing_msg.message_id)
                
            except Exception as e:
                bot.edit_message_text(
                    f"❌ Error generating graph: {str(e)}",
                    call.message.chat.id,
                    processing_msg.message_id
                )
        
        # Show graph options callback
        elif call.data == 'show_graph_options':
            bot.send_message(
                call.message.chat.id,
                "Choose a currency pair for the graph:",
                reply_markup=create_graph_keyboard()
            )
        
        # Answer callback query to remove loading state
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"❌ An error occurred: {str(e)}\n\nPlease try again or use /help."
        )

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages."""
    bot.send_message(
        message.chat.id,
        "I don't understand that command. Please use /help to see available commands."
    )

# Main entry point
if __name__ == "__main__":
    try:
        logger.info("Starting Currency Converter Bot...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")


