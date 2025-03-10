import websocket
import json
import os
import requests
import time
from dotenv import load_dotenv
from rugcheck import rugcheck  # Import the rugcheck function

# Load environment variables
load_dotenv()

api_helius_key = os.getenv("api_helius_key")
RAYDIUM_PROGRAM_ID = os.getenv("RAYDIUM_PROGRAM_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ID_CHAT")

# Configure endpoints
HELIUS_HTTPS_URI_TX = f"https://api.helius.xyz/v0/transactions/?api-key={api_helius_key}"
wss_url = f"wss://mainnet.helius-rpc.com/?api-key={api_helius_key}"

def send_telegram_message(message, retries=3):
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
            return True
        except Exception as e:
            print(f"Telegram send error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return False

def fetch_transaction_details(signature):
    payload = {"transactions": [signature]}
    try:
        response = requests.post(HELIUS_HTTPS_URI_TX, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data[0] if isinstance(data, list) and data else None
    except Exception as e:
        print(f"Transaction fetch error: {e}")
        return None

def extract_token_address(transaction_data):
    try:
        token_transfers = transaction_data.get("tokenTransfers", [])
        for token in token_transfers:
            mint = token.get("mint")
            from_account = token.get("fromTokenAccount")
            if mint and mint != "So11111111111111111111111111111111111111112" and from_account:
                return mint
        return None
    except Exception as e:
        print(f"Address extraction error: {e}")
        return None

def format_rugcheck_message(rc_result, token_mint):
    message = f"📊 *RugCheck Results*\n\n"
    message += f"• *Token Mint:* `{token_mint}`\n"
    message += f"• *Risk Score:* {rc_result['score']}\n"
    message += f"• *Liquidity:* {rc_result['liquidity']:.2f}\n"
    message += f"• *Creator:* `{rc_result['creator']}`\n\n"
    
    message += "*Top Holders (% Supply):*\n"
    message += "\n".join([f"`{p}%`" for p in rc_result['top_holders']]) + "\n\n"
    message += f"*Total Top 10:* `{rc_result['total_percentage']:.2f}%`\n\n"
    message += "⚠️ _This is not financial advice. Always DYOR before investing._"
    return message

def perform_rugcheck(token_mint):
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

        return {
            'score': rc.score,
            'liquidity': rc.totalMarketLiquidity,
            'creator': rc.creator if rc.creator else 'Unknown',
            'top_holders': top_percentages,
            'total_percentage': total_percentage
        }
    except Exception as e:
        print(f"Rugcheck error: {e}")
        return None

def websocket_connection():
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
            return ws
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            time.sleep(5)

def main():
    send_telegram_message("🔔 *Bot Started* - Monitoring Raydium liquidity pools...")
    
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
                        print(f"\n⚠️ New pool detected: {signature}")
                        ws.close()
                        
                        if tx_details := fetch_transaction_details(signature):
                            if token_mint := extract_token_address(tx_details):
                                print(f"🔍 Analyzing token: {token_mint}")
                                
                                if rc_result := perform_rugcheck(token_mint):
                                    telegram_msg = format_rugcheck_message(rc_result, token_mint)
                                    if send_telegram_message(telegram_msg):
                                        print("✅ Notification sent")
                                    else:
                                        print("❌ Failed to send notification")
                                else:
                                    print("⚠️ Rugcheck failed")
                            else:
                                print("⚠️ No valid token mint found")
                        else:
                            print("⚠️ Failed to fetch transaction details")
                        
                        ws = websocket_connection()
        
        except websocket.WebSocketException as e:
            print(f"WebSocket error: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            if ws: ws.close()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
