ILove.py - Solana Liquidity Pool Hunter Bot

ILove.py is a powerful bot that monitors new liquidity pool creations on the Solana blockchain using a WebSocket connection. It extracts token mint addresses, performs a rug check using the rugcheck library, and sends a detailed risk report to a Telegram Chat.


---

🚀 Features

✅ Real-Time Monitoring – Detects new liquidity pools instantly
✅ Rug Check Integration – Analyzes token safety using the rugcheck library
✅ Automated Alerts – Sends Telegram notifications with risk assessment
✅ Secure Configuration – Uses a .env file to store sensitive credentials
✅ Lightweight & Efficient – Runs seamlessly with minimal resource consumption


---

📌 Prerequisites

Before running the bot, ensure you have:

Python 3.8+ installed

A Telegram bot token and chat ID for notifications

A Helius API key for Solana transaction parsing

A .env file to securely store sensitive credentials



---

⚙️ Installation & Setup

1️⃣ Clone the Repository

git clone https://github.com/yourusername/Love4Peace.git
cd Love4Peace

2️⃣ Create a Virtual Environment

To keep dependencies isolated, create and activate a virtual environment:

python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

3️⃣ Install Dependencies

pip install --upgrade pip
pip install -r requirements.txt

4️⃣ Configure Environment Variables

Create a .env file in the root directory and add your credentials:

# Helius API Key
api_helius_key=your_helius_api_key_here

# Raydium Program ID (Solana Liquidity Pool Program)
RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

# Telegram Bot Token & Chat ID
TELEGRAM_SOGE_TOKEN=your_telegram_bot_token_here
ID_CHAT=your_telegram_chat_id_here

⚠️ Important: Never share your .env file. Add it to .gitignore to prevent accidental commits.


---

▶️ Running the Bot

Once the setup is complete, start the bot by running:

python ILove.py

The bot will start listening for new liquidity pools, perform rug checks, and send alerts to your Telegram group.


---

🔍 How It Works

1️⃣ WebSocket Connection: Connects to Solana via Helius API
2️⃣ Liquidity Pool Detection: Listens for newly created pools
3️⃣ Transaction Parsing: Extracts details using the Helius API
4️⃣ Token Mint Address Extraction: Identifies new token contracts
5️⃣ Rug Check Analysis: Verifies token safety with rugcheck
6️⃣ Telegram Notification: Sends a risk report to your chat
7️⃣ Continuous Monitoring: Runs indefinitely, tracking new pools


---

🛠️ Dependencies

The bot relies on the following Python packages:


---

🐞 Troubleshooting

💡 WebSocket Issues: Ensure your Helius API key is valid
💡 Telegram Errors: Check that the bot token and chat ID are correct
💡 Missing Dependencies: Run pip install -r requirements.txt again


---

📜 License

This project is licensed under the MIT License – feel free to modify and contribute!


---

🤝 Contributions & Support

Contributions: Pull requests are welcome!

Issues: If you encounter problems, open an issue on GitHub

Contact: Reach out to the maintainer for further assistance
