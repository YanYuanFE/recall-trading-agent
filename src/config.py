import os
from dotenv import load_dotenv
from typing import Dict, Any
import json

load_dotenv()

class Config:
    # API Configuration
    TRADING_SIM_API_KEY = os.getenv("TRADING_SIM_API_KEY")
    TRADING_SIM_API_URL = os.getenv("TRADING_SIM_API_URL", "https://api.sandbox.competitions.recall.network/api")
    
    # Trading Configuration
    PORTFOLIO_REBALANCE_INTERVAL = int(os.getenv("PORTFOLIO_REBALANCE_INTERVAL", "3600"))
    MAX_SLIPPAGE = float(os.getenv("MAX_SLIPPAGE", "0.01"))
    MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", "10"))
    
    # Risk Management
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.3"))
    STOP_LOSS_THRESHOLD = float(os.getenv("STOP_LOSS_THRESHOLD", "0.05"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.TRADING_SIM_API_KEY:
            raise ValueError("TRADING_SIM_API_KEY is required")
        return True
    
    @classmethod
    def load_portfolio_config(cls, config_path: str = "config/portfolio_config.json") -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Portfolio config file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in portfolio config: {config_path}")

# Validate configuration on import (only if not in testing)
if __name__ != "__main__":
    try:
        Config.validate()
    except Exception:
        # Don't fail on import if config is not set up yet
        pass