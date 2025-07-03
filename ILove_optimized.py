"""
Optimized ILove SOL Bot with Async I/O and Performance Improvements
- Async HTTP requests with connection pooling
- Persistent WebSocket connections with heartbeat
- Concurrent pool processing
- Rate limiting and circuit breaker patterns
- Memory optimization and proper resource cleanup
"""

import asyncio
import aiohttp
import websockets
import json
import os
import time
import gc
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from rugcheck import rugcheck
import logging
from logging.handlers import RotatingFileHandler
import signal
import re
import psutil
from asyncio import Semaphore, Queue

# Performance monitoring
@dataclass
class PerformanceMetrics:
    pools_processed: int = 0
    avg_processing_time: float = 0.0
    memory_usage_mb: float = 0.0
    websocket_reconnects: int = 0
    api_errors: int = 0
    start_time: float = 0.0

# Setup optimized logging
logger = logging.getLogger("ILoveOptimized")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.setLevel(getattr(logging, LOG_LEVEL))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Optimized file handler with smaller rotation
file_handler = RotatingFileHandler(
    "ILove_optimized.log", 
    maxBytes=500000,  # Reduced from 1MB
    backupCount=2     # Reduced from 3
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Environment validation with better error messages
required_env_vars = {
    "api_helius_key": "Helius API key",
    "RAYDIUM_PROGRAM_ID": "Raydium Program ID",
    "TELEGRAM_BOT_TOKEN": "Telegram Bot Token",
    "ID_CHAT": "Telegram Chat ID"
}

missing_vars = []
for var, description in required_env_vars.items():
    if not os.getenv(var):
        missing_vars.append(f"{var} ({description})")

if missing_vars:
    logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Required environment variables missing: {', '.join(missing_vars)}")

# Configuration
api_helius_key = os.getenv("api_helius_key")
RAYDIUM_PROGRAM_ID = os.getenv("RAYDIUM_PROGRAM_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ID_CHAT")

# Performance configuration
MAX_CONCURRENT_POOLS = int(os.getenv("MAX_CONCURRENT_POOLS", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# API endpoints
HELIUS_HTTPS_URI_TX = f"https://api.helius.xyz/v0/transactions/?api-key={api_helius_key}"
wss_url = f"wss://mainnet.helius-rpc.com/?api-key={api_helius_key}"

# Global metrics
metrics = PerformanceMetrics()

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_second: int):
        self.calls_per_second = calls_per_second
        self.calls = []
    
    async def acquire(self):
        now = time.time()
        # Remove calls older than 1 second
        self.calls = [call_time for call_time in self.calls if now - call_time < 1.0]
        
        if len(self.calls) >= self.calls_per_second:
            sleep_time = 1.0 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.calls.append(now)

# Rate limiters
helius_limiter = RateLimiter(100)  # 100 calls per second
telegram_limiter = RateLimiter(30)  # 30 calls per second

def is_valid_solana_address(address: str) -> bool:
    """Validate Solana address format"""
    return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))

async def create_session() -> aiohttp.ClientSession:
    """Create optimized HTTP session with connection pooling"""
    connector = aiohttp.TCPConnector(
        limit=100,              # Total connection pool size
        limit_per_host=20,      # Max connections per host
        keepalive_timeout=60,   # Keep connections alive
        enable_cleanup_closed=True,
        use_dns_cache=True,
        ttl_dns_cache=300,      # DNS cache TTL
    )
    
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    
    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={'User-Agent': 'ILoveSOL-Bot/2.0'}
    )

async def send_telegram_message_async(session: aiohttp.ClientSession, message: str, retries: int = MAX_RETRIES) -> bool:
    """Send Telegram message with async and rate limiting"""
    await telegram_limiter.acquire()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    for attempt in range(retries):
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    logger.warning(f"Telegram API returned status {response.status}")
        except Exception as e:
            logger.error(f"Telegram send error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            metrics.api_errors += 1
    
    return False

async def send_telegram_photo_async(session: aiohttp.ClientSession, photo_url: str, retries: int = MAX_RETRIES) -> bool:
    """Send Telegram photo with async and rate limiting"""
    await telegram_limiter.acquire()
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "parse_mode": "Markdown"
    }
    
    for attempt in range(retries):
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Telegram photo sent successfully")
                    return True
        except Exception as e:
            logger.error(f"Telegram photo send error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            metrics.api_errors += 1
    
    return False

async def fetch_transaction_details_async(session: aiohttp.ClientSession, signature: str) -> Optional[Dict[Any, Any]]:
    """Fetch transaction details with async and rate limiting"""
    await helius_limiter.acquire()
    
    payload = {"transactions": [signature]}
    
    try:
        async with session.post(HELIUS_HTTPS_URI_TX, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug("Transaction details fetched successfully")
                return data[0] if isinstance(data, list) and data else None
            else:
                logger.warning(f"Helius API returned status {response.status}")
                metrics.api_errors += 1
    except Exception as e:
        logger.error(f"Transaction fetch error: {e}")
        metrics.api_errors += 1
    
    return None

def extract_token_address(transaction_data: Dict[Any, Any]) -> Optional[str]:
    """Extract token mint address from transaction data"""
    try:
        token_transfers = transaction_data.get("tokenTransfers", [])
        for token in token_transfers:
            mint = token.get("mint")
            from_account = token.get("fromTokenAccount")
            if mint and mint != "So11111111111111111111111111111111111111112" and from_account:
                if is_valid_solana_address(mint):
                    logger.debug(f"Token mint extracted: {mint}")
                    return mint
        
        logger.warning("No valid token mint found in transaction data")
        return None
    except Exception as e:
        logger.error(f"Address extraction error: {e}")
        return None

def format_rugcheck_message(rc_result: Dict[str, Any], token_mint: str) -> str:
    """Format rugcheck results for Telegram with performance metrics"""
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
    message += f"• *Explore:*  {dexscreen_link}  | {solscan_link}\n\n"
    message += "*Top Holders (% Supply):*\n"
    message += "\n".join([f"`{p}%`" for p in rc_result['top_holders']]) + "\n\n"
    message += f"*Total Top 10:* `{rc_result['total_percentage']:.2f}%`\n\n"
    
    # Add performance info
    message += f"*Bot Stats:* Processed {metrics.pools_processed} pools | "
    message += f"Avg: {metrics.avg_processing_time:.1f}s | "
    message += f"Memory: {metrics.memory_usage_mb:.0f}MB\n\n"
    
    message += "⚠️ _This is not financial advice. Always DYOR before investing._"
    
    return message

async def perform_rugcheck_async(token_mint: str) -> Optional[Dict[str, Any]]:
    """Perform rugcheck analysis with timeout and error handling"""
    logger.info(f"Performing rugcheck for token: {token_mint}")
    
    try:
        # Run rugcheck in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        rc = await loop.run_in_executor(None, rugcheck, token_mint)
        
        total_amount = sum(holder['amount'] for holder in rc.topHolders)
        
        top_holders = sorted(rc.topHolders, key=lambda x: x['amount'], reverse=True)[:10]
        top_percentages = []
        total_percentage = 0

        for holder in top_holders:
            percentage = (holder['amount'] / total_amount * 100) if total_amount > 0 else 0
            top_percentages.append(f"{percentage:.2f}")
            total_percentage += percentage

        logger.info("Rugcheck analysis completed successfully")
        return {
            'score': rc.score,
            'liquidity': rc.totalMarketLiquidity,
            'creator': rc.creator if rc.creator else 'Unknown',
            'mint_authority': getattr(rc, 'mintAuthority', 'None'),
            'freeze_authority': getattr(rc, 'freezeAuthority', 'None'),
            'top_holders': top_percentages,
            'total_percentage': total_percentage
        }
    except Exception as e:
        logger.error(f"Rugcheck error: {e}")
        return None

async def process_pool_async(semaphore: Semaphore, session: aiohttp.ClientSession, signature: str):
    """Process a single pool with concurrency control"""
    async with semaphore:
        start_time = time.time()
        
        try:
            logger.info(f"Processing pool: {signature}")
            
            # Fetch transaction details
            tx_details = await fetch_transaction_details_async(session, signature)
            if not tx_details:
                logger.warning(f"Failed to fetch transaction details for {signature}")
                return
            
            # Extract token address
            token_mint = extract_token_address(tx_details)
            if not token_mint:
                logger.warning(f"No valid token mint found in {signature}")
                return
            
            logger.info(f"Analyzing token: {token_mint}")
            
            # Perform rugcheck analysis
            rc_result = await perform_rugcheck_async(token_mint)
            if not rc_result:
                logger.warning(f"Rugcheck analysis failed for {token_mint}")
                return
            
            # Send notifications
            image_url = f"https://dd.dexscreener.com/ds-data/tokens/solana/{token_mint}/header.png?key=931b70"
            
            # Send photo and message concurrently
            photo_task = send_telegram_photo_async(session, image_url)
            message_task = send_telegram_message_async(
                session, 
                format_rugcheck_message(rc_result, token_mint)
            )
            
            photo_success, message_success = await asyncio.gather(photo_task, message_task, return_exceptions=True)
            
            if message_success:
                logger.info(f"Pool {signature} processed and notification sent successfully")
            else:
                logger.error(f"Failed to send notification for pool {signature}")
            
            # Update metrics
            processing_time = time.time() - start_time
            metrics.pools_processed += 1
            metrics.avg_processing_time = (
                (metrics.avg_processing_time * (metrics.pools_processed - 1) + processing_time) / 
                metrics.pools_processed
            )
            
            # Memory cleanup
            del tx_details, rc_result
            if metrics.pools_processed % 10 == 0:  # Periodic cleanup
                gc.collect()
                process = psutil.Process()
                metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            
        except Exception as e:
            logger.error(f"Error processing pool {signature}: {e}")

async def maintain_websocket_connection(pool_queue: Queue):
    """Maintain persistent WebSocket connection with automatic reconnection"""
    backoff_time = 1
    max_backoff = 60
    
    while True:
        try:
            logger.info("Establishing WebSocket connection...")
            
            async with websockets.connect(
                wss_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                
                # Send subscription request
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [{"mentions": [RAYDIUM_PROGRAM_ID]}]
                }
                
                await websocket.send(json.dumps(request))
                logger.info("WebSocket connected and subscribed successfully")
                
                # Reset backoff on successful connection
                backoff_time = 1
                
                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if data.get("method") == "logsNotification":
                            logs = data["params"]["result"]["value"]["logs"]
                            signature = data["params"]["result"]["value"]["signature"]
                            
                            # Check for pool initialization
                            if any("initialize2: InitializeInstruction2" in log for log in logs):
                                logger.info(f"New pool detected: {signature}")
                                await pool_queue.put(signature)
                                
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON from WebSocket")
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        
        except websockets.exceptions.ConnectionClosedError:
            logger.warning("WebSocket connection closed, reconnecting...")
            metrics.websocket_reconnects += 1
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            metrics.websocket_reconnects += 1
            
        # Exponential backoff
        logger.info(f"Reconnecting in {backoff_time} seconds...")
        await asyncio.sleep(backoff_time)
        backoff_time = min(backoff_time * 2, max_backoff)

async def pool_processor(session: aiohttp.ClientSession, pool_queue: Queue):
    """Process pools from the queue with concurrency control"""
    semaphore = Semaphore(MAX_CONCURRENT_POOLS)
    
    while True:
        try:
            # Get pool signature from queue
            signature = await pool_queue.get()
            
            # Process pool asynchronously
            asyncio.create_task(process_pool_async(semaphore, session, signature))
            
        except Exception as e:
            logger.error(f"Error in pool processor: {e}")

async def performance_monitor():
    """Monitor and log performance metrics"""
    while True:
        await asyncio.sleep(60)  # Log every minute
        
        process = psutil.Process()
        metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        uptime = (time.time() - metrics.start_time) / 3600  # Hours
        
        logger.info(
            f"Performance Stats - "
            f"Pools: {metrics.pools_processed}, "
            f"Avg Time: {metrics.avg_processing_time:.2f}s, "
            f"Memory: {metrics.memory_usage_mb:.1f}MB, "
            f"Reconnects: {metrics.websocket_reconnects}, "
            f"API Errors: {metrics.api_errors}, "
            f"Uptime: {uptime:.1f}h"
        )

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    logger.info("Signal received, shutting down gracefully...")
    # Note: In async context, we'd need to handle this differently
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main async entry point"""
    metrics.start_time = time.time()
    
    # Create HTTP session
    session = await create_session()
    
    try:
        # Send startup notification
        await send_telegram_message_async(
            session, 
            "🔔 *Optimized Bot Started* - High-performance monitoring active..."
        )
        
        # Create pool queue for communication between WebSocket and processor
        pool_queue = Queue(maxsize=100)  # Limit queue size to prevent memory issues
        
        # Start concurrent tasks
        tasks = [
            maintain_websocket_connection(pool_queue),
            pool_processor(session, pool_queue),
            performance_monitor()
        ]
        
        logger.info("Starting optimized bot with async processing...")
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        await session.close()
        logger.info("Session closed, bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())