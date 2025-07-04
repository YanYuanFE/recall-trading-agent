import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.config import Config
import logging
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

@dataclass
class Token:
    address: str
    symbol: str
    chain: str
    decimals: int = 18

@dataclass
class Balance:
    token: Token
    amount: float
    usd_value: float

@dataclass
class Trade:
    from_token: Token
    to_token: Token
    amount: float
    timestamp: float
    tx_hash: Optional[str] = None
    status: str = "pending"

class RecallTradingClient:
    def __init__(self):
        self.api_key = Config.TRADING_SIM_API_KEY
        self.base_url = Config.TRADING_SIM_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        # Disable SSL verification to fix certificate issues
        self.session.verify = False
        
        # Common tokens
        self.tokens = {
            "ethereum": {
                "USDC": Token("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", "ethereum", 6),
                "WETH": Token("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "WETH", "ethereum", 18)
            },
            "solana": {
                "USDC": Token("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "USDC", "solana", 6),
                "SOL": Token("So11111111111111111111111111111111111111112", "SOL", "solana", 9)
            }
        }
    
    def get_portfolio(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/agent/portfolio")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get portfolio: {e}")
            raise
    
    
    def get_account_history(self) -> List[Dict[str, Any]]:
        """Get account history from the new history endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/agent/history")
            response.raise_for_status()
            return response.json().get("history", [])
        except requests.RequestException as e:
            logger.error(f"Failed to get account history: {e}")
            raise

    def get_balances(self) -> List[Balance]:
        try:
            response = self.session.get(f"{self.base_url}/agent/balances")
            response.raise_for_status()
            data = response.json()
            
            balances = []
            for balance_data in data.get("balances", []):
                # New agent/balances endpoint has flat structure
                token = Token(
                    address=balance_data.get("tokenAddress"),
                    symbol=balance_data.get("symbol"),
                    chain=balance_data.get("chain"),
                    decimals=18  # Default, as not provided in response
                )
                
                balance = Balance(
                    token=token,
                    amount=float(balance_data.get("amount", 0)),
                    usd_value=float(balance_data.get("usd_value", 0))
                )
                balances.append(balance)
            
            return balances
        except requests.RequestException as e:
            logger.error(f"Failed to get balances: {e}")
            raise
    
    def get_token_price(self, token_address: str, chain: str) -> float:
        try:
            # Map chain names to the correct format for the API
            if chain == "solana":
                chain_param = "svm"
                specific_chain = "svm"
            elif chain == "ethereum":
                chain_param = "evm"
                specific_chain = "eth"
            else:
                # Default mapping
                chain_param = chain
                specific_chain = chain
            
            params = {
                "token": token_address,
                "chain": chain_param,
                "specificChain": specific_chain
            }
            
            response = self.session.get(f"{self.base_url}/price", params=params)
            response.raise_for_status()
            data = response.json()
            return float(data.get("price", 0))
            
        except requests.RequestException as e:
            logger.error(f"Failed to get token price for {token_address} on {chain}: {e}")
            # Return 0 to allow portfolio calculations to continue
            return 0.0
    
    def get_trade_quote(self, from_token: str, to_token: str, amount: float, chain: str) -> Dict[str, Any]:
        try:
            payload = {
                "fromToken": from_token,
                "toToken": to_token,
                "amount": str(amount),
                "chain": chain
            }
            response = self.session.post(f"{self.base_url}/trade/quote", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get trade quote: {e}")
            raise
    
    def execute_trade(self, from_token: str, to_token: str, amount: float, reason: str = "Portfolio rebalancing") -> Dict[str, Any]:
        try:
            payload = {
                "fromToken": from_token,
                "toToken": to_token,
                "amount": str(amount),
                "reason": reason
            }
            
            response = self.session.post(f"{self.base_url}/trade/execute", json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Trade executed: {amount} {from_token} -> {to_token}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to execute trade: {e}")
            raise
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            params = {"limit": limit}
            response = self.session.get(f"{self.base_url}/agent/trades", params=params)
            response.raise_for_status()
            return response.json().get("trades", [])
        except requests.RequestException as e:
            logger.error(f"Failed to get trade history: {e}")
            raise
    
    def get_competition_status(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/competition/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get competition status: {e}")
            raise
    
    def get_leaderboard(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/competition/leaderboard")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get leaderboard: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def validate_api_key(self) -> bool:
        """Validate if the API key is working by testing multiple endpoints"""
        test_endpoints = [
            "/agent/portfolio",
            "/agent/balances", 
            "/competition/status"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 401:
                    try:
                        error_data = response.json()
                        logger.error(f"API Key validation failed on {endpoint}: {error_data.get('error', 'Unknown error')}")
                    except:
                        logger.error(f"API Key validation failed on {endpoint}: 401 Unauthorized")
                    return False
                elif response.status_code in [200, 404]:
                    # Found a working endpoint
                    logger.debug(f"API Key validation successful on {endpoint}")
                    return True
            except requests.RequestException as e:
                logger.debug(f"Endpoint {endpoint} test failed: {e}")
                continue
        
        logger.error("API Key validation failed: No working endpoints found")
        return False