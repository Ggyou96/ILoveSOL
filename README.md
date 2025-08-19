<div align="center">

# ILoveSOL - Unstable SOL Trading Bot

### 🤖 Telegram Bot for New Liquidity Pool Hunting, Rugchecking & Notifications 💸

</div>

****🔍 How It Works****

This bot is designed to give you an edge in the fast-paced world of Solana trading. It works by:

- **🚀 Starting a WebSocket connection** to the Helius API to monitor the Solana blockchain in real-time.
- **🎣 Targeting the creation of new liquidity pools** on Raydium and Pump.fun.
- **📈 Checking for the most active and latest boosted tokens** on DexScreener.
- **🔎 Extracting the token mint address** and performing a comprehensive rug check using the [rugcheck.xyz](https://rugcheck.xyz) API.
- **🔔 Sending a detailed risk report** directly to your Telegram chat, so you can assess the legitimacy of new tokens before making any moves.

<div align="center">
  <img src="https://github.com/user-attachments/assets/ef417050-39f5-412f-af3d-3752e4cfc1d3" alt="ILoveSOL" width="100%">
</div>

---

******🛠 Prerequisites******

Before getting started, ensure you have the following:

- **Git**
- **Python 3.8+**
- **Helius API Key**: Sign up and get your API key at [Helius](https://www.helius.dev/)
- **Telegram Bot Token**: Create your bot using [BotFather](https://t.me/BotFather)
- **Telegram Chat ID**: Retrieve your chat ID using this handy bot [userinfobot](https://t.me/userinfobot)

---

<div align="center">

*****🚀 Installation*****

<img src="https://github.com/user-attachments/assets/f8fc5f1a-d8e8-43d0-afbb-27b89b35296b" width="360" height="auto" alt="Termux">
<br>
<img src="https://github.com/user-attachments/assets/2a83f91e-78c8-43a1-bfe5-13aa3a866c6e" alt="image" width="30%">

**📱 Android Users:**

[Download Termux](https://play.google.com/store/apps/details?id=com.termux&hl=en&pli=1) from the Play Store to set up a terminal environment.

**Open Termux and run:**

```bash
pkg update && pkg upgrade
pkg install python git nano
```

**Clone the repository:**

```bash
git clone https://github.com/Ggyou96/ILoveSOL.git
cd ILoveSOL
```

**Create your `.env` file:**

Copy the example environment file and then edit it with your details:

```bash
cp envExample .env
nano .env
```

Your `.env` file should look like this:

```
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
ID_CHAT="your-chat-id"
api_helius_key="your-helius-api-key"
```

**Create and activate a Python Virtual Environment:**

```bash
python -m venv .venv
source .venv/bin/activate
```
*(On Windows, use `.venv\Scripts\activate`)*

**Install the dependencies:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

</div>

---

**🤖 Running the Bot**

With your virtual environment activated, start the interactive menu:

```bash
python menu.py
```

From the menu, you can:
- **Start/Stop the Token Hunter**
- **View live logs**
- **Change settings** for sniping and rug checks
- **Exit** the application

⚠️ **ALWAYS DO YOUR OWN RESEARCH!** This tool is for educational purposes only and is not financial advice. ⚠️

---

# 💁‍♂️ Project Structure:

```
ILoveSOL/
├── ILove.py              # Core logic for WebSocket monitoring and token processing.
├── menu.py               # Interactive menu to control the bot.
├── ultimate_utils.py     # Utilities for fetching data from DexScreener.
├── requirements.txt      # Project dependencies.
├── settings_config.json  # Configuration file for snipe and rugcheck options.
├── .env                  # Your secret keys and tokens.
├── envExample            # An example of the .env file.
├── hunter.log            # Log file for the Token Hunter.
├── README.md             # Project documentation.
└── LICENSE               # MIT License.
```

---

### 💡 Contributing

I welcome anyone who wants to collaborate on this project! Since this is my first project on GitHub, I am still learning how to manage contributions. If you'd like to work on this project, feel free to fork the repository, make your changes, and submit a pull request.

---

# ❗ Known Issues

1.  **Risky Tokens Not Being Filtered Properly**: The `perform_rugcheck` function analyzes tokens but does not prevent notifications for high-risk ones.
2.  **No Handling for API Rate Limits**: The script does not detect or handle rate limits from Helius or Telegram APIs.

---

#### 📜 License
This project is licensed under the MIT License.