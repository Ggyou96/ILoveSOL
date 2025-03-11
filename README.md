<div align="center">
  
  *********Telegram Bot  🤖********* <br>
  ******💸 New Liquidity Pool Hunter<br>Rugcheck & Notifications******
<br>

****🔍 How It Works****<br>
****Start a websocket****<br>
****🎣 Target new liquidity pools creation****<br>
****Extract Mint token information. then [rugcheck](https://rugcheck.xyz)****<br>
****🔔 Sends a detailed risk report directly to Telegram chat.****
****rugcheck thier legitimacy before making any moves. 🚀****
****Designed to Hunt new tokens on Raydium, Decentralized Exchange On Solana*****


    
<img src="https://github.com/user-attachments/assets/ef417050-39f5-412f-af3d-3752e4cfc1d3" alt="ILoveSOL" width="100%">

<br>
  
</div>
<br>

******🛠 Prerequisites******
<br><br>
*****Before getting started, ensure you have the following:*****

<br>

- **Git**
- **Python 3.8+**
- **Helius API Key**: Sign up and get your API key at [Helius](https://www.helius.dev/)
- **Telegram Bot Token**: Create your bot using [BotFather](https://t.me/BotFather)
- **Telegram Chat ID**: Retrieve your chat ID using this handy bot [userinfobot](https://t.me/userinfobot) <br> <br><br>


<div align="center"> 
  

*****🚀 Installation*****<br>

<img src="https://github.com/user-attachments/assets/2a83f91e-78c8-43a1-bfe5-13aa3a866c6e" alt="image" width="30%">

*****Android users:*****


[Download Termux](https://play.google.com/store/apps/details?id=com.termux&hl=en&pli=1) from Play Store to set up a terminal environment.<br><br>
***Open Termux***<br>
**run**
<br>
```bash
pkg update && pkg upgrade
```
```bash
pkg install python git nano
```
<br>

***Clone the repository:***
<br>
```bash
git clone https://github.com/Ggyou96/ILoveSOL.git
cd ILoveSOL
```
<br>

**fill in .env with your details:**

<br>

```bash
nano .env
```
<br>

**.env file content:**
<br>


```bash
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
ID_CHAT="your-chat-id"
api_helius_key="your-helius-api-key"
RAYDIUM_PROGRAM_ID="675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" 
```
<br>

***Create a Python Virtual Environment***
<br>

```bash
python -m venv .venv
```
<br>

*****Activate Virtual Environment*****
<br>

****💻 MacOS/Linux 📱Android****
<br>
```bash
source .venv/bin/activate
```
<br>

***🖥️ Microsofot Windows***
<br>
```bash
.venv\Scripts\activate
```
<br>

***Upgrade pip and Install Dependencies:***<br>
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
<br>

***🤖 Running the Bot***
<br>
With your virtual environment activated, simply run:

```bash
python ILove.py
```

Your bot will start sending you notifications for new liquidity pool creations once it performs its checks.
<br><br>
⚠️ [ALWAYS DO YOUR RESEARCH!](https://rugcheck.xyz)
<br> <br> </div>
  
# 💁‍♂️ Project Structure:

```
ILoveSOL/
├── ILove.py          # Main bot script
├── requirements.txt  # Dependencies
├── .env              # Details such as API keys and tokens (should not be shared!)
├── README.md         # Project documentation
└── LICENSE           # Legal information about usage
```

### 💡 Contributing
I welcome anyone who wants to collaborate on this project! Since this is my first project on GitHub, I am still learning how to manage contributions. If you'd like to work on this project, follow these steps:
##### 📥 Get a Local Copy
```bash
git clone https://github.com/Ggyou96/ILoveSOL.git
````
###### Create a separate directory (optional)
Instead of navigating into the project folder, you can copy it into a new directory:
```bash
mkdir X  # Replace 'X' with your preferred directory name
cp -r ILoveSOL/* X/
```
Now, the project is available inside X/.

🚀 How to Contribute
Feel free to modify the code and improve it.
If you make changes and want to share them, 
you can:
        Fork the repository.
        Make your changes.
        Submit a pull request (PR).
<br>
I am still new to GitHub collaboration, I appreciate any suggestions on improving the process. 😊
        
# ❗ Known Issues

1. **Risky Tokens Not Being Filtered Properly**
   - The `perform_rugcheck` function analyzes tokens but does not prevent notifications for high-risk ones.
2. **WebSocket Connection Drops**
   - The WebSocket may fail to reconnect after multiple disconnections.
3. **Telegram Message Delivery Issues**
   - The bot retries 3 times on failure but does not store failed messages for later retries.
4. **Transaction Fetching Errors**
   - If the API request to fetch transaction details fails, it only prints an error.
5. **No Handling for API Rate Limits**
   - The script does not detect or handle rate limits from Helius or Telegram APIs.

#### 📜 License MIT License.



