"""
Performance Configuration for ILove SOL Bot
Environment-based settings for optimal performance
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    # Network settings
    max_concurrent_pools: int = 5
    request_timeout: int = 5
    max_retries: int = 3
    connection_pool_size: int = 100
    connection_per_host: int = 20
    keepalive_timeout: int = 60
    
    # Rate limiting
    helius_rate_limit: int = 100  # calls per second
    telegram_rate_limit: int = 30  # calls per second
    
    # Memory management
    log_max_size: int = 500000  # 500KB
    log_backup_count: int = 2
    gc_frequency: int = 10  # garbage collect every N pools
    
    # Processing
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10
    queue_max_size: int = 100
    
    # Monitoring
    stats_update_interval: int = 60  # seconds
    performance_log_level: str = "INFO"

def get_performance_config() -> PerformanceConfig:
    """Get performance configuration based on environment"""
    
    # Detect environment
    environment = os.getenv("BOT_ENVIRONMENT", "production").lower()
    
    if environment == "development":
        return PerformanceConfig(
            max_concurrent_pools=2,
            request_timeout=10,
            max_retries=2,
            connection_pool_size=50,
            helius_rate_limit=50,
            telegram_rate_limit=15,
            log_max_size=1000000,  # 1MB for debugging
            performance_log_level="DEBUG"
        )
    
    elif environment == "testing":
        return PerformanceConfig(
            max_concurrent_pools=3,
            request_timeout=3,
            max_retries=1,
            connection_pool_size=20,
            helius_rate_limit=20,
            telegram_rate_limit=10,
            log_max_size=100000,  # 100KB
            performance_log_level="WARNING"
        )
    
    elif environment == "high_performance":
        return PerformanceConfig(
            max_concurrent_pools=10,
            request_timeout=3,
            max_retries=2,
            connection_pool_size=200,
            connection_per_host=50,
            helius_rate_limit=150,
            telegram_rate_limit=50,
            gc_frequency=5,  # More frequent cleanup
            performance_log_level="ERROR"
        )
    
    else:  # production (default)
        return PerformanceConfig()

def get_system_optimized_config() -> PerformanceConfig:
    """Get configuration optimized for current system specs"""
    import psutil
    
    # Get system specs
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    base_config = get_performance_config()
    
    # Adjust based on system specs
    if cpu_count >= 8 and memory_gb >= 16:
        # High-spec system
        base_config.max_concurrent_pools = min(15, cpu_count * 2)
        base_config.connection_pool_size = 200
        base_config.helius_rate_limit = 150
    elif cpu_count >= 4 and memory_gb >= 8:
        # Medium-spec system
        base_config.max_concurrent_pools = min(8, cpu_count * 2)
        base_config.connection_pool_size = 100
        base_config.helius_rate_limit = 100
    else:
        # Low-spec system
        base_config.max_concurrent_pools = 3
        base_config.connection_pool_size = 50
        base_config.helius_rate_limit = 50
        base_config.telegram_rate_limit = 15
    
    return base_config

# Environment variables mapping
ENV_MAPPING = {
    "MAX_CONCURRENT_POOLS": ("max_concurrent_pools", int),
    "REQUEST_TIMEOUT": ("request_timeout", int),
    "MAX_RETRIES": ("max_retries", int),
    "CONNECTION_POOL_SIZE": ("connection_pool_size", int),
    "HELIUS_RATE_LIMIT": ("helius_rate_limit", int),
    "TELEGRAM_RATE_LIMIT": ("telegram_rate_limit", int),
    "LOG_MAX_SIZE": ("log_max_size", int),
    "LOG_BACKUP_COUNT": ("log_backup_count", int),
    "GC_FREQUENCY": ("gc_frequency", int),
    "WEBSOCKET_PING_INTERVAL": ("websocket_ping_interval", int),
    "WEBSOCKET_PING_TIMEOUT": ("websocket_ping_timeout", int),
    "QUEUE_MAX_SIZE": ("queue_max_size", int),
    "STATS_UPDATE_INTERVAL": ("stats_update_interval", int),
    "PERFORMANCE_LOG_LEVEL": ("performance_log_level", str),
}

def apply_env_overrides(config: PerformanceConfig) -> PerformanceConfig:
    """Apply environment variable overrides to configuration"""
    
    for env_var, (attr_name, type_func) in ENV_MAPPING.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                setattr(config, attr_name, type_func(env_value))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Invalid value for {env_var}: {env_value} ({e})")
    
    return config

def get_final_config() -> PerformanceConfig:
    """Get final configuration with all optimizations and overrides applied"""
    
    # Start with system-optimized config
    config = get_system_optimized_config()
    
    # Apply environment overrides
    config = apply_env_overrides(config)
    
    # Validate configuration
    config = validate_config(config)
    
    return config

def validate_config(config: PerformanceConfig) -> PerformanceConfig:
    """Validate and sanitize configuration values"""
    
    # Ensure reasonable limits
    config.max_concurrent_pools = max(1, min(50, config.max_concurrent_pools))
    config.request_timeout = max(1, min(30, config.request_timeout))
    config.max_retries = max(0, min(10, config.max_retries))
    config.connection_pool_size = max(10, min(1000, config.connection_pool_size))
    config.connection_per_host = max(5, min(100, config.connection_per_host))
    config.helius_rate_limit = max(1, min(200, config.helius_rate_limit))
    config.telegram_rate_limit = max(1, min(100, config.telegram_rate_limit))
    config.log_max_size = max(10000, min(10000000, config.log_max_size))
    config.log_backup_count = max(1, min(10, config.log_backup_count))
    config.gc_frequency = max(1, min(100, config.gc_frequency))
    config.queue_max_size = max(10, min(1000, config.queue_max_size))
    
    # Ensure connection per host doesn't exceed pool size
    if config.connection_per_host > config.connection_pool_size:
        config.connection_per_host = config.connection_pool_size // 2
    
    return config

def print_config_summary(config: PerformanceConfig):
    """Print configuration summary"""
    print("🔧 Performance Configuration Summary:")
    print("-" * 40)
    print(f"Environment: {os.getenv('BOT_ENVIRONMENT', 'production')}")
    print(f"Max Concurrent Pools: {config.max_concurrent_pools}")
    print(f"Request Timeout: {config.request_timeout}s")
    print(f"Connection Pool Size: {config.connection_pool_size}")
    print(f"Helius Rate Limit: {config.helius_rate_limit}/s")
    print(f"Telegram Rate Limit: {config.telegram_rate_limit}/s")
    print(f"Log Level: {config.performance_log_level}")
    print("-" * 40)

# Export common configurations
DEVELOPMENT_CONFIG = get_performance_config()
PRODUCTION_CONFIG = get_performance_config()
HIGH_PERFORMANCE_CONFIG = PerformanceConfig(
    max_concurrent_pools=15,
    request_timeout=3,
    connection_pool_size=200,
    helius_rate_limit=150,
    telegram_rate_limit=50,
    performance_log_level="ERROR"
)

if __name__ == "__main__":
    # Test configuration
    config = get_final_config()
    print_config_summary(config)