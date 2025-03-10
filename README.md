# Currency Converter Bot

This is a Telegram bot for converting currencies and viewing exchange rate trends. It uses the FastForex API for real-time currency conversion and historical exchange rate data.

## Features
- Real-time currency conversion
- Historical exchange rate graphs
- Support for multiple currency pairs
- Custom currency pair input

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   ```

2. **Navigate to the project directory**:
   ```bash
   cd telegram_alikhan_bot_projects/Include
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

5. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Create a `.env` file** in the `Include` directory with the following content:
   ```
   BOT_TOKEN=<your_bot_token>
   API_KEY=<your_api_key>
   ```

7. **Run the bot**:
   ```bash
   python 3_bot_telegram.py
   ```

## Note
Ensure that your `.env` file is not included in version control to keep your API keys and tokens secure.
