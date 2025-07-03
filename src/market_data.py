import requests
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from src.trading_client import RecallTradingClient
from src.config import Config

logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    symbol: str
    price: float
    timestamp: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None

@dataclass
class MarketStats:
    symbol: str
    price: float
    market_cap: Optional[float]
    volume_24h: Optional[float]
    change_24h: Optional[float]
    change_7d: Optional[float]
    timestamp: float

class MarketDataProvider:
    def __init__(self):
        self.trading_client = RecallTradingClient()
        self.price_cache = {}
        self.cache_duration = 60  # 1 minute cache
        
    def get_token_price(self, token_address: str, chain: str) -> Optional[float]:
        cache_key = f"{token_address}_{chain}"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_duration:
                return cached_data['price']
        
        try:
            price = self.trading_client.get_token_price(token_address, chain)
            
            # Update cache
            self.price_cache[cache_key] = {
                'price': price,
                'timestamp': current_time
            }
            
            return price
            
        except Exception as e:
            logger.error(f"Failed to get price for {token_address} on {chain}: {e}")
            return None
    
    def get_multiple_prices(self, tokens: List[Dict[str, str]]) -> Dict[str, float]:
        prices = {}
        
        for token in tokens:
            symbol = token.get('symbol')
            address = token.get('address')
            chain = token.get('chain')
            
            if symbol and address and chain:
                price = self.get_token_price(address, chain)
                if price is not None:
                    prices[symbol] = price
        
        return prices
    
    def get_price_history(self, symbol: str, hours: int = 24) -> List[PriceData]:
        # In a real implementation, you would fetch historical data
        # For now, we'll simulate with current price
        try:
            current_price = self.get_current_price_by_symbol(symbol)
            if current_price is None:
                return []
            
            # Simulate historical data (in production, fetch real historical data)
            price_history = []
            current_time = time.time()
            
            for i in range(hours):
                # Add some random variation for simulation
                variation = 1 + (hash(f"{symbol}_{i}") % 100 - 50) / 1000  # ±5% variation
                simulated_price = current_price * variation
                
                price_data = PriceData(
                    symbol=symbol,
                    price=simulated_price,
                    timestamp=current_time - (i * 3600)  # i hours ago
                )
                price_history.append(price_data)
            
            return list(reversed(price_history))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Failed to get price history for {symbol}: {e}")
            return []
    
    def get_current_price_by_symbol(self, symbol: str) -> Optional[float]:
        # Map symbol to token address and chain
        token_map = {
            'WETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'chain': 'ethereum'},
            'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'chain': 'ethereum'},
            'SOL': {'address': 'So11111111111111111111111111111111111111112', 'chain': 'solana'}
        }
        
        if symbol in token_map:
            token_info = token_map[symbol]
            return self.get_token_price(token_info['address'], token_info['chain'])
        
        return None
    
    def calculate_price_change(self, symbol: str, hours: int = 24) -> Optional[float]:
        try:
            price_history = self.get_price_history(symbol, hours + 1)
            
            if len(price_history) < 2:
                return None
            
            current_price = price_history[-1].price
            past_price = price_history[0].price
            
            if past_price > 0:
                change = (current_price - past_price) / past_price
                return change
            
        except Exception as e:
            logger.error(f"Failed to calculate price change for {symbol}: {e}")
        
        return None
    
    def get_market_summary(self) -> Dict[str, MarketStats]:
        symbols = ['WETH', 'USDC', 'SOL']
        market_summary = {}
        
        for symbol in symbols:
            try:
                current_price = self.get_current_price_by_symbol(symbol)
                change_24h = self.calculate_price_change(symbol, 24)
                change_7d = self.calculate_price_change(symbol, 168)  # 7 days
                
                if current_price is not None:
                    market_stats = MarketStats(
                        symbol=symbol,
                        price=current_price,
                        market_cap=None,  # Would need additional API for this
                        volume_24h=None,  # Would need additional API for this
                        change_24h=change_24h,
                        change_7d=change_7d,
                        timestamp=time.time()
                    )
                    market_summary[symbol] = market_stats
                    
            except Exception as e:
                logger.error(f"Failed to get market stats for {symbol}: {e}")
        
        return market_summary
    
    def get_volatility(self, symbol: str, hours: int = 24) -> Optional[float]:
        try:
            price_history = self.get_price_history(symbol, hours)
            
            if len(price_history) < 2:
                return None
            
            prices = [p.price for p in price_history]
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    return_val = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(return_val)
            
            if not returns:
                return None
            
            # Calculate standard deviation of returns (volatility)
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            return volatility
            
        except Exception as e:
            logger.error(f"Failed to calculate volatility for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        # Crypto markets are always open, but you might want to check
        # for maintenance windows or other factors
        return True
    
    def get_support_resistance_levels(self, symbol: str, hours: int = 168) -> Dict[str, float]:
        try:
            price_history = self.get_price_history(symbol, hours)
            
            if len(price_history) < 10:
                return {}
            
            prices = [p.price for p in price_history]
            
            # Simple support and resistance calculation
            max_price = max(prices)
            min_price = min(prices)
            avg_price = sum(prices) / len(prices)
            
            # Calculate support and resistance levels
            resistance_1 = avg_price + (max_price - avg_price) * 0.618  # Fibonacci retracement
            support_1 = avg_price - (avg_price - min_price) * 0.618
            
            return {
                'resistance': resistance_1,
                'support': support_1,
                'max_price': max_price,
                'min_price': min_price,
                'avg_price': avg_price
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate support/resistance for {symbol}: {e}")
            return {}

class PriceMonitor:
    def __init__(self, price_change_threshold: float = 0.05):
        self.market_data = MarketDataProvider()
        self.price_change_threshold = price_change_threshold
        self.last_prices = {}
        self.alerts = []
        
    def monitor_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        alerts = []
        
        for symbol in symbols:
            try:
                current_price = self.market_data.get_current_price_by_symbol(symbol)
                
                if current_price is None:
                    continue
                
                if symbol in self.last_prices:
                    last_price = self.last_prices[symbol]
                    change = (current_price - last_price) / last_price
                    
                    if abs(change) >= self.price_change_threshold:
                        alert = {
                            'symbol': symbol,
                            'type': 'price_change',
                            'current_price': current_price,
                            'last_price': last_price,
                            'change': change,
                            'timestamp': time.time()
                        }
                        alerts.append(alert)
                        logger.info(f"Price alert: {symbol} changed {change:.2%}")
                
                self.last_prices[symbol] = current_price
                
            except Exception as e:
                logger.error(f"Error monitoring price for {symbol}: {e}")
        
        return alerts
    
    def get_price_alerts(self) -> List[Dict[str, Any]]:
        return self.alerts.copy()
    
    def clear_alerts(self):
        self.alerts.clear()