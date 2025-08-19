# token_utils.py

import json
import requests
import time
from datetime import datetime
from itertools import islice
from threading import Thread
from typing import List, Dict, Any

class DexScreener:
    def __init__(self, valid_tokens_path='valid_tokens.json', output_path='data_tokens.json', chain_id='solana'):
        self.valid_tokens_path = valid_tokens_path
        self.output_path = output_path
        self.chain_id = chain_id
        self.api_url = "https://api.dexscreener.com/tokens/v1/{chainId}/{addresses}"
        self.rate_limit_delay = 0.2
        self.max_retries = 3
        self.max_concurrent_positions = self.load_max_concurrent_positions()

    def load_max_concurrent_positions(self) -> int:
        try:
            with open('settings_config.json', 'r') as f:
                config = json.load(f)
                return config.get('settings_config', {}).get('max_concurrent_positions', 1)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Warning] Failed to load trade_config.json: {e}. Using default max_concurrent_positions=1")
            return 1

    def load_valid_tokens(self) -> List[str]:
        try:
            with open(self.valid_tokens_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Error] Failed to load valid tokens: {e}")
            return []

    def chunks(self, iterable, size):
        it = iter(iterable)
        while chunk := list(islice(it, size)):
            yield chunk

    def fetch_token_data(self, addresses: List[str]) -> List[Dict[str, Any]]:
        url = self.api_url.format(chainId=self.chain_id, addresses=",".join(addresses))
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
                print(f"[Error] Failed to fetch data: {e}")
                return []

    def process_token_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_data = []
        now = int(time.time())
        for item in raw_data:
            try:
                websites = [{"label": s.get("label", ""), "url": s.get("url", "")} for s in item.get("info", {}).get("websites", [])]
                socials = [{"type": s.get("type", ""), "url": s.get("url", "")} for s in item.get("info", {}).get("socials", [])]
                cleaned = {
                    "chain_id": item.get("chainId", ""),
                    "dex_id": item.get("dexId", ""),
                    "pair_address": item.get("pairAddress", ""),
                    "url": item.get("url", ""),
                    "created_at": item.get("pairCreatedAt", 0),
                    "token_mint": item.get("baseToken", {}).get("address", ""),
                    "token_name": item.get("baseToken", {}).get("name", ""),
                    "token_symbol": item.get("baseToken", {}).get("symbol", ""),
                    "quote_token": {
                        "address": item.get("quoteToken", {}).get("address", ""),
                        "name": item.get("quoteToken", {}).get("name", ""),
                        "symbol": item.get("quoteToken", {}).get("symbol", "")
                    },
                    "price_native": item.get("priceNative", "0"),
                    "price_usd": item.get("priceUsd", "0"),
                    "price_change": {
                        "m5": item.get("priceChange", {}).get("m5", 0),
                        "h1": item.get("priceChange", {}).get("h1", 0),
                        "h6": item.get("priceChange", {}).get("h6", 0),
                        "h24": item.get("priceChange", {}).get("h24", 0)
                    },
                    "transactions": {
                        "buys": {
                            "m5": item.get("txns", {}).get("m5", {}).get("buys", 0),
                            "h1": item.get("txns", {}).get("h1", {}).get("buys", 0),
                            "h6": item.get("txns", {}).get("h6", {}).get("buys", 0),
                            "h24": item.get("txns", {}).get("h24", {}).get("buys", 0)
                        },
                        "sells": {
                            "m5": item.get("txns", {}).get("m5", {}).get("sells", 0),
                            "h1": item.get("txns", {}).get("h1", {}).get("sells", 0),
                            "h6": item.get("txns", {}).get("h6", {}).get("sells", 0),
                            "h24": item.get("txns", {}).get("h24", {}).get("sells", 0)
                        }
                    },
                    "volume": {
                        "m5": item.get("volume", {}).get("m5", 0),
                        "h1": item.get("volume", {}).get("h1", 0),
                        "h6": item.get("volume", {}).get("h6", 0),
                        "h24": item.get("volume", {}).get("h24", 0)
                    },
                    "liquidity": {
                        "usd": item.get("liquidity", {}).get("usd", 0),
                        "base": item.get("liquidity", {}).get("base", 0),
                        "quote": item.get("liquidity", {}).get("quote", 0)
                    },
                    "market_cap": item.get("marketCap", 0),
                    "fdv": item.get("fdv", 0),
                    "info": {
                        "image_url": item.get("info", {}).get("imageUrl", ""),
                        "header_image": item.get("info", {}).get("header", ""),
                        "open_graph": item.get("info", {}).get("openGraph", ""),
                        "websites": websites,
                        "socials": socials
                    },
                    "boosts": item.get("boosts", {}).get("active", 0),
                    "last_updated": now,
                    "fetch_timestamp": now
                }
                cleaned_data.append(cleaned)
            except Exception as e:
                print(f"[Error] Processing token: {e}")
                continue
        return cleaned_data

    def update_data_tokens(self):
        tokens = self.load_valid_tokens()
        if not tokens:
            print("[Warning] No tokens found")
            return
        all_raw_data = []
        for chunk in self.chunks(tokens, 30):
            data = self.fetch_token_data(chunk)
            if data:
                all_raw_data.extend(data)
            time.sleep(self.rate_limit_delay)
        cleaned = self.process_token_data(all_raw_data)
        try:
            with open(self.output_path, 'w') as f:
                json.dump(cleaned, f, indent=2)
            print(f"[Success] Saved {len(cleaned)} tokens")
        except Exception as e:
            print(f"[Error] Writing file: {e}")

        # Call TokenSelector with max_concurrent_positions
        selector = TokenSelector(cleaned, self.max_concurrent_positions)
        selector.update_selected_tokens()

    def start_scheduler(self):
        def loop():
            while True:
                self.update_data_tokens()
                time.sleep(300)
        Thread(target=loop, daemon=True).start()

class TokenSelector:
    def __init__(self, tokens: List[Dict[str, Any]], max_positions: int = 1):
        self.tokens = tokens
        self.max_positions = max_positions
        self.sol_price = 160.0024905  # Default SOL price, can be updated from API
        self.sol_mint = "So11111111111111111111111111111111111111112"

    def score_token(self, token):
        try:
            score = 0
            reasons = []

            # Price change scoring
            price_change_h1 = float(token["price_change"]["h1"])
            price_change_h24 = float(token["price_change"]["h24"])
            
            if price_change_h1 > 0:
                score += price_change_h1 * 0.5
                reasons.append(f"Price up {price_change_h1:.2f}% (1h)")
            
            if price_change_h24 > 0:
                score += price_change_h24 * 0.3
                reasons.append(f"Price up {price_change_h24:.2f}% (24h)")

            # Buy/sell ratio scoring
            buys_h1 = float(token["transactions"]["buys"]["h1"])
            sells_h1 = float(token["transactions"]["sells"]["h1"])
            buy_sell_ratio = buys_h1 / (sells_h1 + 1)  # Add 1 to avoid division by zero
            
            if buy_sell_ratio > 1.5:
                score += min(buy_sell_ratio, 5)  # Cap the bonus at 5
                reasons.append(f"Buy pressure (ratio: {buy_sell_ratio:.2f})")
            elif buy_sell_ratio < 0.8:
                score -= 1
                reasons.append(f"Sell pressure (ratio: {buy_sell_ratio:.2f})")

            # Volume scoring
            volume_h1 = float(token["volume"]["h1"])
            if volume_h1 > 50000:
                score += 1
                reasons.append("Strong 1h volume")
            elif volume_h1 < 1000:
                score -= 1
                reasons.append("Low 1h volume")

            # Liquidity scoring
            liquidity = float(token["liquidity"]["usd"])
            if liquidity > 1000000:
                score += 2
                reasons.append("Good liquidity (>$1M)")
            elif liquidity > 100000:
                score += 1
                reasons.append("Decent liquidity (>$100K)")
            elif liquidity < 50000:
                score -= 1
                reasons.append("Low liquidity (<$50K)")

            # Market cap consideration
            market_cap = float(token["market_cap"])
            if market_cap > 100000000 and score > 0:
                score += 1  # Bonus for established tokens with positive indicators

            return round(score, 2), reasons
        except Exception as e:
            print(f"[Error] Scoring token {token.get('token_symbol', 'unknown')}: {e}")
            return 0, [f"Error scoring: {e}"]

    def determine_priority(self, score: float) -> str:
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        elif score >= 0:
            return "low"
        else:
            return "avoid"

    def update_selected_tokens(self):
        start_time = time.time()
        analysis_time = datetime.now().isoformat()
        scored_tokens = []
        
        # First pass to get SOL price if available
        for token in self.tokens:
            if token["token_mint"] == self.sol_mint:
                try:
                    self.sol_price = float(token["price_usd"])
                except:
                    pass

        # Score all tokens
        for token in self.tokens:
            if token["token_mint"] == self.sol_mint:
                continue  # Skip SOL itself
                
            score, reasons = self.score_token(token)
            priority = self.determine_priority(score)
            
            token_data = {
                "token_info": {
                    "name": token["token_name"],
                    "symbol": token["token_symbol"],
                    "mint": token["token_mint"]
                },
                "metrics": {
                    "price": float(token["price_usd"]),
                    "price_change": round(float(token["price_change"]["h24"]), 2),
                    "liquidity": round(float(token["liquidity"]["usd"]), 2),
                    "market_cap": round(float(token["market_cap"]), 2),
                    "volume_m5": round(float(token["volume"]["m5"]), 2),
                    "volume_h1": round(float(token["volume"]["h1"]), 2),
                    "volume_h6": round(float(token["volume"]["h6"]), 2),
                    "volume_h24": round(float(token["volume"]["h24"]), 2),
                    "buys_m5": float(token["transactions"]["buys"]["m5"]),
                    "sells_m5": float(token["transactions"]["sells"]["m5"]),
                    "buy_sell_ratio": round(float(token["transactions"]["buys"]["m5"]) / 
                                      (float(token["transactions"]["sells"]["m5"]) + 1), 2)
                },
                "analysis": {
                    "score": score,
                    "reasons": reasons,
                    "priority": priority
                },
                "timestamp": datetime.now().isoformat()
            }
            scored_tokens.append(token_data)

        # Sort tokens by score in descending order
        scored_tokens.sort(key=lambda x: x["analysis"]["score"], reverse=True)
        
        # Select only the top N tokens based on max_concurrent_positions
        selected_tokens = scored_tokens[:self.max_positions]
        
        # Prepare the final output structure
        output = {
            "metadata": {
                "sol_price": self.sol_price,
                "sol_mint": self.sol_mint,
                "analysis_time": analysis_time,
                "processing_stats": {
                    "total_tokens": len(scored_tokens),
                    "processed": len(scored_tokens),
                    "errors": 0,
                    "analysis_duration_sec": round(time.time() - start_time, 2)
                },
                "max_concurrent_positions": self.max_positions,
                "selected_tokens_count": len(selected_tokens)
            },
            "tokens": selected_tokens
        }

        try:
            with open('tokens.json', 'w') as f:
                json.dump(output, f, indent=2)
            print(f"[Info] Selected {len(selected_tokens)} tokens (max_concurrent_positions={self.max_positions})")
        except Exception as e:
            print(f"[Error] Saving tokens.json: {e}")

if __name__ == "__main__":
    dex = DexScreener()
    dex.start_scheduler()
    while True:
        time.sleep(1)
