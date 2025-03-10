## 💸 ILoveSOL Telegram Bot

# Solana Raydium New Liquidity Hunter 🤖

This Telegram bot is designed to hunt for Solana Raydium tokens and perform rug checks. It opens a websocket to monitor new liquidity pool creations. Once a new pool is detected, the bot pauses the websocket, processes the transaction to extract the mint token, performs a rug check, and then sends you a clear, comprehensive report right in your Telegram chat.
# 🌟 Features
- Real-Time Notifications: Monitors new liquidity pool events on the Solana blockchain via a websocket.
- Token Analysis: Extracts the mint token from transactions and performs a rug check.
- Detailed Reports: Sends concise, easy-to-read notifications directly to your Telegram chat.
# 🛠 Prerequisites
Before getting started, ensure you have the following:
- Helius API Key: Sign up and get your API key at Helius.
- Telegram Bot Token: Create your bot using BotFather.
- Telegram Chat ID: Retrieve your chat ID using this handy bot.
- Python 3.8+
- Git

* For Android users:
Download Termux from the Google Play Store to set up a terminal environment.

# 📁 This project consists of three main files:
```
ILoveSOL/
├── ILove.py          # Main bot script
├── requirements.txt  # Dependencies
├── .env              # Details such as API keys and tokens (should not be shared!)
├── README.md         # Project documentation
└── LICENSE           # Legal information about usage
```

# 🚀 Installation
* Android (Using Termux)
```bash
pkg update && pkg upgrade
```
```bash
pkg install python git nano
```
**🔗    
```bash
git clone https://github.com/Ggyou96/ILoveSOL.git
```
```bash
cd ILoveSOL
```
Fill in your details for.env File 
```bash
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
ID_CHAT = "your-chat-id"
api_helius_key = "your-helius-api-key"
RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" 
```
```bash
nano .env
```
Create a Python Virtual Environment:
```bash
python -m venv .venv
```
Activate Virtual Environment:
* MacOS/Linux/Androird:
```bash
source .venv/bin/activate
```
* Windows:
```bash
.venv\Scripts\activate
````
Upgrade pip and Install Dependencies:
```bash
pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
# Running the Bot
With your virtual environment activated, 
simply run:
```bash
python ILove.py
```
Your bot will start send you notifications for new liquidity pool creations once it performs its checks.
Feel free to contribute, open issues, or suggest improvements. Happy coding and enjoy your bot!

## ALWAYS DO YOUR REASEARCH



