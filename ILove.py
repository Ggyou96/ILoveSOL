import websocket
import json
import os
import requests
import time
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import signal
import re
from rugcheck import rugcheck
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from ultimate_utils import DexScreener
from telegram import Bot
from telegram.error import TelegramError

# Setup logging
logger = logging.getLogger("UltimateHunter")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)



# Load environment variables
load_dotenv()

# Constants
CONFIG_FILE = 'settings_config.json'
VALID_TOKENS_FILE = 'valid_tokens.json'
UNCHECKED_TOKENS_FILE = 'unchecked_tokens.json'
API_ENDPOINT_MOST_ACTIVE = 'https://api.dexscreener.com/token-boosts/top/v1'
API_ENDPOINT_LATEST = 'https://api.dexscreener.com/token-profiles/latest/v1'
TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

# Initialize DexScreener client
dex_screener = DexScreener()

# Initialize Telegram bot if credentials are available
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
telegram_bot = Bot(token=telegram_bot_token) if telegram_bot_token else None

# Check for required environment variables
required_vars = ["api_helius_key"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
    exit(1)

api_helius_key = os.getenv("api_helius_key")

# Configure endpoints
HELIUS_HTTPS_URI_TX = f"https://api.helius.xyz/v0/transactions/?api-key={api_helius_key}"
wss_url = f"wss://mainnet.helius-rpc.com/?api-key={api_helius_key}"

def is_valid_solana_address(address):
    """Validate Solana address format."""
    return re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address) is not None

def load_config():
    """Load the configuration from the config file."""
    try:
        if not os.path.exists(CONFIG_FILE):
            logger.error(f"Config file '{CONFIG_FILE}' not found.")
            return None
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def send_telegram_message(message, parse_mode="Markdown"):
    """Send a message to Telegram."""
    if not telegram_bot_token or not telegram_chat_id:
        logger.warning("Telegram credentials not configured, skipping notification")
        return False
    
    try:
        url = TELEGRAM_API_URL.format(telegram_bot_token)
        payload = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def send_telegram_photo(image_url):
    """Send a photo to Telegram."""
    if not telegram_bot or not telegram_chat_id:
        logger.warning("Telegram credentials not configured, skipping photo")
        return False
    
    try:
        telegram_bot.send_photo(
            chat_id=telegram_chat_id, 
            photo=image_url,
            caption="Token Image"
        )
        return True
    except TelegramError as e:
        logger.error(f"Failed to send Telegram photo: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram photo: {e}")
        return False

def fetch_dexscreener_data(token_mint):
    """Fetch token data from Dexscreener using token_utils."""
    try:
        # Get fresh data from DexScreener
        dex_screener.update_data_tokens()
        
        # Load the updated data
        with open('data_tokens.json', 'r') as f:
            tokens_data = json.load(f)
        
        # Find our token
        token_data = next((t for t in tokens_data if t['token_mint'] == token_mint), None)
        
        if not token_data:
            return {}
            
        return {
            "token_name": token_data.get("token_name"),
            "symbol": token_data.get("token_symbol"),
            "dexId": token_data.get("dex_id"),
            "price_usd": token_data.get("price_usd"),
            "liquidity": token_data.get("liquidity", {}).get("usd"),
            "marketCap": token_data.get("market_cap"),
            "imageUrl": token_data.get("info", {}).get("image_url"),
            "openGraph": token_data.get("info", {}).get("open_graph"),
            "websites": token_data.get("info", {}).get("websites", []),
            "pair_address": token_data.get("pair_address"),
            "url": token_data.get("url")
        }
    except Exception as e:
        logger.error(f"Error fetching Dexscreener data: {e}")
        return {}

def format_passcheck_message(token_address, rc_result, dexscreener_data, config):
    """Format a message for tokens that pass rug check."""
    message = "✅ *Token Passed Rug Check*\n\n"
    message += f"• *Token Mint:* `{token_address}`\n"
    message += f"• *Risk Score:* {getattr(rc_result, 'score', 'N/A')}\n"
    
    if dexscreener_data:
        message += f"• *Name:* {dexscreener_data.get('token_name', 'N/A')}\n"
        message += f"• *Symbol:* {dexscreener_data.get('symbol', 'N/A')}\n"
        message += f"• *DEX ID:* {dexscreener_data.get('dexId', 'N/A')}\n"
        
        price = dexscreener_data.get('price_usd')
        message += f"• *Price:* ${price}\n" if price else "• *Price:* N/A\n"
        
        liquidity = dexscreener_data.get('liquidity')
        message += f"• *Liquidity:* ${liquidity:,.2f}\n" if liquidity else "• *Liquidity:* N/A\n"
        
        market_cap = dexscreener_data.get('marketCap')
        message += f"• *Market Cap:* ${market_cap:,.2f}\n" if market_cap else "• *Market Cap:* N/A\n"
        
        # Add websites if available
        websites = dexscreener_data.get('websites', [])
        if websites:
            message += "\n• *Websites:*\n"
            for site in websites:
                message += f"  - [{site.get('label', 'Link')}]({site.get('url')})\n"
    
    # Always include Solscan and Dexscreener links
    links = [
        f"[Solscan](https://solscan.io/token/{token_address})",
        f"[Dexscreener](https://dexscreener.com/solana/{token_address})"
    ]
    
    if dexscreener_data.get('url'):
        links[1] = f"[Dexscreener]({dexscreener_data['url']})"
    
    message += f"\n• *Links:* {' | '.join(links)}\n"
    
    # Add image if enabled and available
    if config.get('send_token_image', False) and dexscreener_data.get('imageUrl'):
        message += f"\n![Token Image]({dexscreener_data['imageUrl']})"
    
    message += "\n⚠️ _This is not financial advice. Always DYOR before investing._"
    return message

def get_active_programs(config):
    """Return active programs and their instructions based on config."""
    active_programs = []
    snipe_config = config.get('snipe_options', {})
    
    if snipe_config.get('raydium', False):
        active_programs.append({
            'id': 'rad1',
            'name': 'Raydium',
            'program': snipe_config['program_ids']['raydium'],
            'instruction': snipe_config['instructions']['raydium'],
            'source': 'raydium'
        })
    
    if snipe_config.get('pump_fun', False):
        active_programs.append({
            'id': 'pump1',
            'name': 'Pump.fun',
            'program': snipe_config['program_ids']['pump_fun'],
            'instruction': snipe_config['instructions']['pump_fun'],
            'source': 'pump_fun'
        })
    
    return active_programs

def perform_rug_check(token_address, config, max_retries=3):
    """Perform a rug check on the given token address with retry logic."""
    failure_reasons = []
    rc_result = None
    
    if not is_valid_solana_address(token_address):
        failure_reasons.append("Invalid token address format")
        return False, failure_reasons, None
        
    for attempt in range(max_retries):
        try:
            time.sleep(0.5 * (attempt + 1))  # Increasing delay between retries
            rc = rugcheck(token_address)
            rc_result = rc
            
            if not rc:
                failure_reasons.append("Rugcheck returned no data")
                continue  # Try again if no data
                
            # Check mint authority
            if config['rugcheck_config']['check_mint_authority']:
                if hasattr(rc,'mintAuthority') and rc.mintAuthority and rc.mintAuthority != 'disabled':
                    failure_reasons.append(f"Mint authority enabled ({rc.mintAuthority})")
            
            # Check freeze authority
            if config['rugcheck_config']['check_freeze_authority']:
                if hasattr(rc, 'freezeAuthority') and rc.freezeAuthority and rc.freezeAuthority != 'disabled':
                    failure_reasons.append(f"Freeze authority enabled ({rc.freezeAuthority})")
            
            # Check top holders
            if config['rugcheck_config']['check_top_holders']:
                top_holders_percentage = 0
                if hasattr(rc, 'topHolders'):
                    if isinstance(rc.topHolders, dict):
                        top_holders_percentage = float(rc.topHolders.get('totalPercentage', 0))
                    elif isinstance(rc.topHolders, list) and len(rc.topHolders) > 0:
                        for holder in rc.topHolders:
                            if isinstance(holder, dict) and 'percentage' in holder:
                                top_holders_percentage += float(holder['percentage'])
                
                max_percentage = config['rugcheck_config']['max_top_holders_percentage']
                if top_holders_percentage > max_percentage:
                    failure_reasons.append(f"Top holders control too much ({top_holders_percentage}% > {max_percentage}%)")
            
            # Check risk score
            if hasattr(rc,'score') and rc.score is not None:
                risk_threshold = config['rugcheck_config']['risk_score_threshold']
                if float(rc.score) > risk_threshold:
                    failure_reasons.append(f"Risk score too high ({rc.score} > {risk_threshold})")
            
            if failure_reasons:
                return False, failure_reasons, rc_result
            return True, [], rc_result
            
        except json.JSONDecodeError:
            if attempt == max_retries - 1:  # Last attempt
                failure_reasons.append("Rugcheck service returned invalid data")
            continue
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                failure_reasons.append(f"Network error during rugcheck: {str(e)}")
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                failure_reasons.append(f"Unexpected rugcheck error: {str(e)}")
            continue
    
    return False, failure_reasons, rc_result

def save_token_to_file(token_address, filename):
    """Save token address to specified file."""
    try:
        existing_tokens = []
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as f:
                try: 
                    existing_tokens = json.load(f)
                    if not isinstance(existing_tokens, list):
                        existing_tokens = []
                except json.JSONDecodeError:
                    existing_tokens = []
        
        if token_address not in existing_tokens:
            existing_tokens.append(token_address)
            with open(filename, 'w') as f:
                json.dump(existing_tokens, f, indent=4)
            logger.info(f"Saved token to {filename}: {token_address}")
    except Exception as e:
        logger.error(f"Error saving token {token_address} to {filename}: {e}")

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
        return None

def extract_token_address(transaction_data, source):
    """Extract token mint address from transaction data."""
    try:
        if source == "raydium":
            # First try to find token transfers
            token_transfers = transaction_data.get("tokenTransfers", [])
            for token in token_transfers:
                mint = token.get("mint")
                from_account = token.get("fromTokenAccount")
                if mint and mint != "So11111111111111111111111111111111111111112" and from_account:
                    logger.debug(f"Token mint extracted: {mint}")
                    return mint
            
            # If no token transfers found, look for token initialization in instructions
            instructions = transaction_data.get("instructions", [])
            for instruction in instructions:
                if instruction.get("program") == "spl-token":
                    parsed = instruction.get("parsed", {})
                    if parsed.get("type") == "initializeMint":
                        mint = parsed.get("info", {}).get("mint")
                        if mint:
                            logger.debug(f"Token mint extracted from initialization: {mint}")
                            return mint
        
        elif source == "pump_fun":
            # For pump.fun, the token mint is typically in the accountKeys
            account_keys = transaction_data.get("accountKeys", [])
            token_mint = account_keys[-1] if len(account_keys) > 0 else None
            if token_mint and is_valid_solana_address(token_mint):
                return token_mint
        
        logger.warning("No valid token mint found in transaction data.")
        return None
    except Exception as e:
        logger.error(f"Address extraction error: {e}")
        return None

def websocket_connection(active_programs, max_retries=5, initial_backoff=5):
    """Establish a WebSocket connection with exponential backoff and max retries."""
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            ws = websocket.create_connection(wss_url, timeout=30)
            
            # Create subscriptions for all active programs
            subscriptions = [{"mentions": [p['program']]} for p in active_programs]
            
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": subscriptions
            }
            
            ws.send(json.dumps(request))
            logger.info("WebSocket connected successfully")
            print("WebSocket connected successfully")
            return ws
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Re-raise if we've exhausted retries
            logger.error(f"WebSocket connection failed (attempt {attempt + 1}): {e}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)  # Cap backoff at 60 seconds
    return None

def signal_handler(sig, frame):
    """Handle termination signals to shut down gracefully."""
    logger.info("Signal received, shutting down gracefully...")
    if telegram_bot_token and telegram_chat_id:
        send_telegram_message("🛑 UltimateHunter is shutting down...")
    exit(0)

def get_solana_token_addresses_most_active(config):
    """Get the Solana token addresses from the most active boosts API and perform rug checks."""
    try:
        response = requests.get(API_ENDPOINT_MOST_ACTIVE)
        response.raise_for_status()
        
        data = response.json()
        boosts = data if isinstance(data, list) else [data]
        
        solana_addresses = [
            item.get('tokenAddress') 
            for item in boosts 
            if isinstance(item, dict) and item.get('chainId', '').lower() =='solana'
        ]
        
        if not solana_addresses:
            logger.info("No Solana token addresses found in most active boosts.")
            return
        
        logger.info(f"Found {len(solana_addresses)} Solana tokens from most active boosts. Performing rug checks...")
        
        for token_address in solana_addresses:
            if not token_address:
                continue
                
            logger.info(f"\nChecking token: {token_address}")
            is_valid, failure_reasons, rc_result = perform_rug_check(token_address, config)
            
            if is_valid:
                logger.info("Token passed rug check")
                save_token_to_file(token_address, VALID_TOKENS_FILE)
                if telegram_bot_token and telegram_chat_id:
                    dexscreener_data = fetch_dexscreener_data(token_address)
                    message = format_passcheck_message(token_address, rc_result, dexscreener_data, config['rugcheck_config'])
                    if send_telegram_message(message):
                        if config['rugcheck_config'].get('send_token_image', False) and dexscreener_data.get('imageUrl'):
                            send_telegram_photo(dexscreener_data['imageUrl'])
            else:
                logger.info("Token failed rug check")
                if failure_reasons:
                    logger.info("Reasons:")
                    for reason in failure_reasons:
                        logger.info(f" - {reason}")
                save_token_to_file(token_address, UNCHECKED_TOKENS_FILE)
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making API request for most active boosts: {e}")
    except ValueError as e:
        logger.error(f"Error parsing JSON response for most active boosts: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in most active boosts check: {e}")

def get_solana_token_addresses_latest(config):
    """Get the Solana token addresses from the latest boosted tokens API and perform rug checks."""
    try:
        response = requests.get(API_ENDPOINT_LATEST)
        response.raise_for_status()
        
        data = response.json()
        
        # The response is a list of token profiles
        if not isinstance(data, list):
            logger.error("Unexpected API response format for latest boosted tokens")
            return
            
        solana_addresses = [
            token.get('tokenAddress') 
            for token in data 
            if isinstance(token, dict) and token.get('chainId', '').lower() == 'solana'
        ]
        
        if not solana_addresses:
            logger.info("No Solana token addresses found in latest boosted tokens.")
            return
        
        logger.info(f"Found {len(solana_addresses)} latest boosted Solana tokens. Performing rug checks...")
        
        for token_address in solana_addresses:
            if not token_address:
                continue
                
            logger.info(f"\nChecking token: {token_address}")
            is_valid, failure_reasons, rc_result = perform_rug_check(token_address, config)
            
            if is_valid:
                logger.info("Token passed rug check")
                save_token_to_file(token_address, VALID_TOKENS_FILE)
                if telegram_bot_token and telegram_chat_id:
                    dexscreener_data = fetch_dexscreener_data(token_address)
                    message = format_passcheck_message(token_address, rc_result, dexscreener_data, config['rugcheck_config'])
                    if send_telegram_message(message):
                        if config['rugcheck_config'].get('send_token_image', False) and dexscreener_data.get('imageUrl'):
                            send_telegram_photo(dexscreener_data['imageUrl'])
            else:
                logger.info("Token failed rug check")
                if failure_reasons:
                    logger.info("Reasons:")
                    for reason in failure_reasons:
                        logger.info(f" - {reason}")
                save_token_to_file(token_address, UNCHECKED_TOKENS_FILE)
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making API request for latest boosted tokens: {e}")
    except ValueError as e:
        logger.error(f"Error parsing JSON response for latest boosted tokens: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in latest boosted tokens check: {e}")

def run_boosted_tokens_check(config):
    """Run checks for boosted tokens (most active and latest) in parallel."""
    logger.info("Starting boosted tokens check...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(get_solana_token_addresses_most_active, config),
            executor.submit(get_solana_token_addresses_latest, config)
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in boosted tokens check: {e}")
    logger.info("Boosted tokens check completed.")

def process_new_pool(signature, logs, active_program, config):
    """Process a new pool detection."""
    program_name = active_program['name']
    source = active_program['source']
    instruction = active_program['instruction']
    
    logger.info(f"New {program_name} pool detected: {signature}")
    print(f"\n⚠️ New {program_name} pool detected: {signature}")
    
    if tx_details := fetch_transaction_details(signature):
        if token_mint := extract_token_address(tx_details, source):
            if is_valid_solana_address(token_mint):
                logger.info(f"New token mint found: {token_mint}")
                print(f"✅ New token mint: {token_mint}")
                
                try:
                    is_valid, failure_reasons, rc_result = perform_rug_check(token_mint, config)
                    
                    if is_valid:
                        logger.info("Token passed rug check")
                        print("✅ Token passed rug check")
                        save_token_to_file(token_mint, VALID_TOKENS_FILE)
                        if telegram_bot_token and telegram_chat_id:
                            dexscreener_data = fetch_dexscreener_data(token_mint)
                            message = f"✅ *New Token Passed Rug Check*\n\n"
                            message += f"• *Source:* {program_name}\n"
                            message += format_passcheck_message(token_mint, rc_result, dexscreener_data, config['rugcheck_config'])
                            if send_telegram_message(message):
                                if config['rugcheck_config'].get('send_token_image', False) and dexscreener_data.get('imageUrl'):
                                    send_telegram_photo(dexscreener_data['imageUrl'])
                    else:
                        logger.info("Token failed rug check")
                        print("❌ Token failed rug check")
                        if failure_reasons:
                            logger.info("Reasons:")
                            print("Reasons:")
                            for reason in set(failure_reasons):
                                logger.info(f" - {reason}")
                                print(f" - {reason}")
                        save_token_to_file(token_mint, UNCHECKED_TOKENS_FILE)
                except Exception as e:
                    logger.error(f"Rugcheck failed after retries: {e}")
                    print(f"⚠️ Rugcheck failed after retries: {e}")
                    save_token_to_file(token_mint, UNCHECKED_TOKENS_FILE)
            else:
                logger.warning(f"Invalid Solana address detected: {token_mint}")
                print(f"⚠️ Invalid Solana address: {token_mint}")
        else:
            logger.info("No new token mint found in this transaction")
            print("ℹ️ No new token mint found in this transaction")
    else:
        logger.warning("Failed to fetch transaction details.")
        print("⚠️ Failed to fetch transaction details")

def run_websocket_monitoring(active_programs, config):
    """Run the websocket monitoring for Raydium and Pump.fun."""
    program_info = {p['program']: p for p in active_programs}
    
    logger.info(f"Starting WebSocket monitoring - Monitoring: {', '.join([p['name'] for p in active_programs])}")
    print(f"Starting WebSocket monitoring - Monitoring: {', '.join([p['name'] for p in active_programs])}")
    
    while True:
        ws = None
        try:
            ws = websocket_connection(active_programs)
            while True:
                message = ws.recv()
                data = json.loads(message)
                
                if data.get("method") == "logsNotification":
                    logs = data["params"]["result"]["value"]["logs"]
                    signature = data["params"]["result"]["value"]["signature"]
                    
                    # Check which program this belongs to
                    for program in active_programs:
                        program_id = program['program']
                        instruction = program['instruction']
                        
                        if any(program_id in log for log in logs) and any(instruction in log for log in logs):
                            process_new_pool(signature, logs, program, config)
                            break
        
        except websocket.WebSocketTimeoutException:
            logger.warning("WebSocket timeout, reconnecting...")
            time.sleep(5)
            continue
        except websocket.WebSocketConnectionClosedException:
            logger.warning("WebSocket connection closed, reconnecting...")
            time.sleep(5)
            continue
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
            print("\n🛑 Shutting down...")
            if ws: 
                try:
                    ws.close()
                except Exception:
                    pass
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass

def main():
    # Initialize token files if they don't exist
    for filename in [VALID_TOKENS_FILE, UNCHECKED_TOKENS_FILE]:
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump([], f, indent=4)
    
    # Load config
    config = load_config()
    if not config:
        logger.error("Failed to load config, exiting.")
        return
    
    # Send startup notification
    if telegram_bot_token and telegram_chat_id:
        send_telegram_message("🚀 UltimateHunter is starting up...")
    
    snipe_config = config.get('snipe_options', {})
    
    # Check if we should run boosted tokens check
    if snipe_config.get('boosted', False):
        # Run boosted tokens check in a separate thread
        boosted_thread = threading.Thread(target=run_boosted_tokens_check, args=(config,))
        boosted_thread.daemon = True
        boosted_thread.start()
    
    # Get active programs for websocket monitoring
    active_programs = get_active_programs(config)
    
    # If we have active programs for websocket monitoring, start it
    if active_programs:
        run_websocket_monitoring(active_programs, config)
    elif not snipe_config.get('boosted', False):
        logger.error("No snipe options enabled in config. Please enable at least one in settings.")
        return

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()
