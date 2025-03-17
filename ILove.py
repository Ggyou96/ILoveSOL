import websocket
import json
import os
import requests
import time
from dotenv import load_dotenv
from rugcheck import rugcheck  # Import the rugcheck function
import logging
from logging.handlers import RotatingFileHandler
import signal
import re  # NEW: Added import for input validation

# Setup logging
logger = logging.getLogger("ILove")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation
file_handler = RotatingFileHandler("ILove.log", maxBytes=1000000, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("api_helius_key"):
    logger.error("Missing environment variable: api_helius_key")
if not os.getenv("RAYDIUM_PROGRAM_ID"):
    logger.error("Missing environment variable: RAYDIUM_PROGRAM_ID")
if not os.getenv("TELEGRAM_BOT_TOKEN"):
    logger.error("Missing environment variable: TELEGRAM_BOT_TOKEN")
if not os.getenv("ID_CHAT"):
    logger.error("Missing environment variable: ID_CHAT")

api_helius_key = os.getenv("api_helius_key")
RAYDIUM_PROGRAM_ID = os.getenv("RAYDIUM_PROGRAM_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ID_CHAT")

# Configure endpoints
HELIUS_HTTPS_URI_TX = f"https://api.helius.xyz/v0/transactions/?api-key={api_helius_key}"
wss_url = f"wss://mainnet.helius-rpc.com/?api-key={api_helius_key}"

def is_valid_solana_address(address):  # NEW: Input validation
    return re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address) is not None

def send_telegram_message(message, retries=3):
    """Send a message to the specified Telegram chat."""
    logger.info(f"Preparing to send telegram message: {message}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Telegram send error (attempt {attempt+1}): {e}")
            print(f"Telegram send error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return False

def fetch_transaction_details(signature):
    """Fetch transaction details from the Helius API."""
    logger.debug(f"Fetching transaction details for signature: {signature}")
    payload = {"transactions": [signature]}
    try:
        response = requests.post(HELIUS_HTTPS_URI_TX, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.debug("Transaction details fetched successfully.")
        return data[0] if isinstance(data, list) and data else None
    except Exception as e:
        logger.error(f"Transaction fetch error: {e}")
        print(f"Transaction fetch error: {e}")
        return None

def extract_token_address(transaction_data):
    """Extract token mint address from transaction data."""
    try:
        token_transfers = transaction_data.get("tokenTransfers", [])
        for token in token_transfers:
            mint = token.get("mint")
            from_account = token.get("fromTokenAccount")
            if mint and mint != "So11111111111111111111111111111111111111112" and from_account:
                logger.debug(f"Token mint extracted: {mint}")
                return mint
        logger.warning("No valid token mint found in transaction data.")
        return None
    except Exception as e:
        logger.error(f"Address extraction error: {e}")
        print(f"Address extraction error: {e}")
        return None

def format_rugcheck_message(rc_result, token_mint):
    solscan_link = f"[Solscan](https://solscan.io/token/{token_mint})"
    dexscreen_link = f"[DexScreener](https://dexscreener.com/solana/{token_mint})"
    
    risk_label = "🚨 HIGH RISK" if rc_result['score'] > 75 else "⚠️ MEDIUM RISK" if rc_result['score'] > 40 else "✅ LOW RISK"
    
    message = f"📊 *RugCheck Results*\n\n"
    message += f"• *Token Mint:* `{token_mint}`\n"
    message += f"• *Risk Score:* {rc_result['score']} ({risk_label})\n"
    message += f"• *Liquidity:* {rc_result['liquidity']:.2f}\n"
    message += f"• *Creator:* `{rc_result['creator']}`\n"
    message += f"• *Mint Authority:* `{rc_result['mint_authority']}`\n"
    message += f"• *Freeze Authority:* `{rc_result['freeze_authority']}`\n\n"
    message += f"• *Explore:* {solscan_link} | {dexscreen_link}\n\n"
    message += "*Top Holders (% Supply):*\n"
    message += "\n".join([f"`{p}%`" for p in rc_result['top_holders']]) + "\n\n"
    message += f"*Total Top 10:* `{rc_result['total_percentage']:.2f}%`\n\n"
    message += "⚠️ _This is not financial advice. Always DYOR before investing._"
    logger.debug("Formatted rugcheck message.")
    return message

def perform_rugcheck(token_mint):
    """Perform a rugcheck analysis on the given token mint."""
    logger.info(f"Performing rugcheck for token: {token_mint}")
    try:
        rc = rugcheck(token_mint)
        total_amount = sum(holder['amount'] for holder in rc.topHolders)
        
        top_holders = sorted(rc.topHolders, key=lambda x: x['amount'], reverse=True)[:10]
        top_percentages = []
        total_percentage = 0

        for holder in top_holders:
            percentage = (holder['amount'] / total_amount * 100) if total_amount > 0 else 0
            top_percentages.append(f"{percentage:.2f}")
            total_percentage += percentage

        logger.info("Rugcheck analysis completed successfully.")
        return {
            'score': rc.score,
            'liquidity': rc.totalMarketLiquidity,
            'creator': rc.creator if rc.creator else 'Unknown',
            'mint_authority': rc.mintAuthority if hasattr(rc, 'mintAuthority') else 'None',
            'freeze_authority': rc.freezeAuthority if hasattr(rc, 'freezeAuthority') else 'None',
            'top_holders': top_percentages,
            'total_percentage': total_percentage
        }
    except Exception as e:
        logger.error(f"Rugcheck error: {e}")
        print(f"Rugcheck error: {e}")
        return None

def websocket_connection():
    """Establish a WebSocket connection with exponential backoff."""
    backoff = 5  # initial backoff time in seconds
    while True:
        try:
            ws = websocket.create_connection(wss_url, timeout=30)
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [{"mentions": [RAYDIUM_PROGRAM_ID]}]
            }
            ws.send(json.dumps(request))
            print("WebSocket connected successfully")
            logger.info("WebSocket connected successfully")
            backoff = 5  # reset backoff time on success
            return ws
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            print(f"WebSocket connection failed: {e}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)  # increase backoff time, max 60 seconds

def signal_handler(sig, frame):
    """Handle termination signals to shut down gracefully."""
    logger.info("Signal received, shutting down gracefully...")
    send_telegram_message("🔔 *Bot Stopped* - Monitoring terminated.")
    exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    send_telegram_message("🔔 *Bot Started* - Monitoring Raydium liquidity pools...")
    logger.info("Bot started and monitoring Raydium liquidity pools.")
    
    while True:
        ws = None
        try:
            ws = websocket_connection()
            while True:
                message = ws.recv()
                data = json.loads(message)
                
                if data.get("method") == "logsNotification":
                    logs = data["params"]["result"]["value"]["logs"]
                    signature = data["params"]["result"]["value"]["signature"]
                    
                    if any("initialize2: InitializeInstruction2" in log for log in logs):
                        logger.info(f"New pool detected: {signature}")
                        print(f"\n⚠️ New pool detected: {signature}")
                        ws.close()
                        
                        if tx_details := fetch_transaction_details(signature):
                            if token_mint := extract_token_address(tx_details):
                                # NEW: Validate the token mint address before analysis
                                if not is_valid_solana_address(token_mint):
                                    logger.warning(f"Invalid Solana address detected: {token_mint}")
                                    print(f"⚠️ Invalid Solana address: {token_mint}")
                                    ws = websocket_connection()
                                    continue
                                logger.info(f"Analyzing token: {token_mint}")
                                print(f"🔍 Analyzing token: {token_mint}")
                                
                                if rc_result := perform_rugcheck(token_mint):
                                    telegram_msg = format_rugcheck_message(rc_result, token_mint)
                                    if send_telegram_message(telegram_msg):
                                        logger.info("Notification sent successfully.")
                                        print("✅ Notification sent")
                                    else:
                                        logger.error("Failed to send telegram notification.")
                                        print("❌ Failed to send notification")
                                else:
                                    logger.warning("Rugcheck analysis failed.")
                                    print("⚠️ Rugcheck failed")
                            else:
                                logger.warning("No valid token mint found.")
                                print("⚠️ No valid token mint found")
                        else:
                            logger.warning("Failed to fetch transaction details.")
                            print("⚠️ Failed to fetch transaction details")
                        
                        ws = websocket_connection()
        
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            print(f"WebSocket error: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
            print("\n🛑 Shutting down...")
            if ws: ws.close()
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
