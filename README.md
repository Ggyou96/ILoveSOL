ILoveSOL Bot
This Telegram bot is designed to hunt for Solana Raydium tokens and perform rug checks. It opens a websocket to monitor new liquidity pool creations. Once a new pool is detected, the bot pauses the websocket, processes the transaction to extract the mint token, performs a rug check, and then sends you a clear, comprehensive report right in your Telegram chat.
Features
• Real-Time Notifications: Monitors new liquidity pool events on the Solana blockchain via a websocket.
• Token Analysis: Extracts the mint token from transactions and performs a rug check.
• Detailed Reports: Sends concise, easy-to-read notifications directly to your Telegram chat.
Prerequisites
Before getting started, ensure you have the following:
• Helius API Key: Sign up and get your API key at Helius.
• Telegram Bot Token: Create your bot using BotFather.
• Telegram Chat ID: Retrieve your chat ID using this handy bot.
• Python 3.8+
• Git
For Android users:
Download Termux from the Google Play Store to set up a terminal environment.
Project Files
This project consists of three main files:
• ILove.py: The main script for the Telegram bot.
• requirements.txt: Lists the Python dependencies (to be installed using pip).
• .env: Contains configuration details such as API keys and tokens.
Example .env File
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token" ID_CHAT = "your-chat-id" api_helius_key = "your-helius-api-key" # Public Raydium Program ID RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" 
Installation
Android (Using Termux)
• Open Termux and update your packages: pkg update && pkg upgrade 
• Install Python and Git: pkg install python git 
Windows, macOS, or Linux
• Clone the Repository:
git clone https://github.com/Ggyou96/ILoveSOL.git cd ILoveSOL 
• Configure the .env File:
• Open the file: nano .env 
• Fill in your details for TELEGRAM_BOT_TOKEN, ID_CHAT, and api_helius_key.
• Save and exit (Ctrl + X, then Y, then Enter).
• Create a Python Virtual Environment:
python -m venv .venv 
• Activate the Virtual Environment:
• On macOS/Linux: source .venv/bin/activate 
• On Windows: .venv\Scripts\activate 
• Upgrade pip and Install Dependencies:
pip install --upgrade pip pip install -r requirements.txt 
Running the Bot
With your virtual environment activated, simply run:
python ILove.py 
Your bot will start monitoring for new liquidity pool creations and send you notifications once it performs its checks.
Feel free to contribute, open issues, or suggest improvements. Happy coding and enjoy your bot!




