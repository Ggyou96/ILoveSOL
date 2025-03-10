![ILoveSOL](https://github.com/user-attachments/assets/ef417050-39f5-412f-af3d-3752e4cfc1d3)

# ILoveSOL Telegram Bot  🤖 
## 💸 New Liquidity Pool Hunter and Do rugcheck
This Telegram bot is designed to hunt for Solana Raydium tokens and perform rug checks. It opens a websocket to monitor new liquidity pool creations. Once a new pool is detected, the bot pauses the websocket, processes the transaction to extract the mint token, performs a rug check, and then sends you a clear, comprehensive report right in your Telegram chat.
## ⚠️ ALWAYS DO YOUR RESEARCH!

🌟 Features

- **Real-Time Notifications**: Monitors new liquidity pool events on the Solana blockchain via a websocket.
- **Token Analysis**: Extracts the mint token from transactions and performs a rug check.
- **Detailed Reports**: Sends concise, easy-to-read notifications directly to your Telegram chat.

# 🛠 Prerequisites

Before getting started, ensure you have the following:

- **Helius API Key**: Sign up and get your API key at Helius.
- **Telegram Bot Token**: Create your bot using BotFather.
- **Telegram Chat ID**: Retrieve your chat ID using this handy bot.
- **Python 3.8+**
- **Git**

*For Android users:* Download Termux from the Google Play Store to set up a terminal environment.

# 💁‍♂️ Project Structure:

```
ILoveSOL/
├── ILove.py          # Main bot script
├── requirements.txt  # Dependencies
├── .env              # Details such as API keys and tokens (should not be shared!)
├── README.md         # Project documentation
└── LICENSE           # Legal information about usage
```

# 🚀 Installation

### Android (Using Termux)

```bash
pkg update && pkg upgrade
pkg install python git nano
```

Clone the repository:

```bash
git clone https://github.com/Ggyou96/ILoveSOL.git
cd ILoveSOL
```

Create a `.env` file and fill in your details:

```bash
nano .env
```

Example `.env` file content:

```bash
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
ID_CHAT="your-chat-id"
api_helius_key="your-helius-api-key"
RAYDIUM_PROGRAM_ID="675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" 
```

Create a Python Virtual Environment:

```bash
python -m venv .venv
```

Activate Virtual Environment:

- MacOS/Linux/Android:

```bash
source .venv/bin/activate
```

- Windows:

```bash
.venv\Scripts\activate
```

Upgrade pip and Install Dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

# 🤖 Running the Bot

With your virtual environment activated, simply run:

```bash
python ILove.py
```

Your bot will start sending you notifications for new liquidity pool creations once it performs its checks.

# ❗ Known Issues

1. **Risky Tokens Not Being Filtered Properly**

   - The `perform_rugcheck` function analyzes tokens but does not prevent notifications for high-risk ones.
   - **Possible fix:** Implement a risk threshold to filter out high-risk tokens.

2. **WebSocket Connection Drops**

   - The WebSocket may fail to reconnect after multiple disconnections.
   - **Possible fix:** Use exponential backoff for reconnection attempts.

3. **Telegram Message Delivery Issues**

   - The bot retries 3 times on failure but does not store failed messages for later retries.
   - **Possible fix:** Implement logging and message queueing for failed attempts.

4. **Transaction Fetching Errors**

   - If the API request to fetch transaction details fails, it only prints an error.
   - **Possible fix:** Add retry logic with increasing delay.

5. **No Handling for API Rate Limits**

   - The script does not detect or handle rate limits from Helius or Telegram APIs.
   - **Possible fix:** Detect rate limit responses and apply exponential backoff.

# 📜 License

This project is licensed under the MIT License.

## ⚠️ ALWAYS DO YOUR RESEARCH!

