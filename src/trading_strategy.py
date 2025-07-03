import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from src.trading_client import RecallTradingClient
from src.config import Config

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    action: str  # 'buy', 'sell', 'hold'
    symbol: str
    strength: float  # 0-1
    reason: str
    timestamp: float

class TradingStrategy(ABC):
    def __init__(self):
        self.trading_client = RecallTradingClient()
        
    @abstractmethod
    def generate_signals(self) -> List[Signal]:
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, available_capital: float) -> float:
        pass

class MomentumStrategy(TradingStrategy):
    def __init__(self, lookback_period: int = 24, momentum_threshold: float = 0.05):
        super().__init__()
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.price_history = {}
        
    def generate_signals(self) -> List[Signal]:
        signals = []
        
        try:
            # Get current balances to determine what tokens we have
            balances = self.trading_client.get_balances()
            
            for balance in balances:
                if balance.token.symbol in ['USDC']:  # Skip stablecoin
                    continue
                    
                signal = self._analyze_momentum(balance.token.symbol, balance.token.address, balance.token.chain)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating momentum signals: {e}")
            
        return signals
    
    def _analyze_momentum(self, symbol: str, token_address: str, chain: str) -> Optional[Signal]:
        try:
            # Get current price
            current_price = self.trading_client.get_token_price(token_address, chain)
            
            # Store price history (in real implementation, you'd want persistent storage)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append({
                'price': current_price,
                'timestamp': time.time()
            })
            
            # Keep only recent prices
            cutoff_time = time.time() - (self.lookback_period * 3600)  # lookback_period in hours
            self.price_history[symbol] = [
                p for p in self.price_history[symbol] 
                if p['timestamp'] > cutoff_time
            ]
            
            if len(self.price_history[symbol]) < 2:
                return None
            
            # Calculate momentum
            prices = [p['price'] for p in self.price_history[symbol]]
            
            if len(prices) >= 2:
                recent_return = (prices[-1] - prices[0]) / prices[0]
                
                if recent_return > self.momentum_threshold:
                    return Signal(
                        action='buy',
                        symbol=symbol,
                        strength=min(abs(recent_return), 1.0),
                        reason=f"Positive momentum: {recent_return:.2%}",
                        timestamp=time.time()
                    )
                elif recent_return < -self.momentum_threshold:
                    return Signal(
                        action='sell',
                        symbol=symbol,
                        strength=min(abs(recent_return), 1.0),
                        reason=f"Negative momentum: {recent_return:.2%}",
                        timestamp=time.time()
                    )
            
            return Signal(
                action='hold',
                symbol=symbol,
                strength=0.0,
                reason="No significant momentum",
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing momentum for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, signal: Signal, available_capital: float) -> float:
        # Position size based on signal strength and risk management
        base_position_size = available_capital * 0.1  # 10% of available capital
        position_size = base_position_size * signal.strength
        
        # Apply maximum position size limit
        max_position = available_capital * Config.MAX_POSITION_SIZE
        return min(position_size, max_position)

class MeanReversionStrategy(TradingStrategy):
    def __init__(self, lookback_period: int = 48, z_score_threshold: float = 2.0):
        super().__init__()
        self.lookback_period = lookback_period
        self.z_score_threshold = z_score_threshold
        self.price_history = {}
        
    def generate_signals(self) -> List[Signal]:
        signals = []
        
        try:
            balances = self.trading_client.get_balances()
            
            for balance in balances:
                if balance.token.symbol in ['USDC']:
                    continue
                    
                signal = self._analyze_mean_reversion(balance.token.symbol, balance.token.address, balance.token.chain)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating mean reversion signals: {e}")
            
        return signals
    
    def _analyze_mean_reversion(self, symbol: str, token_address: str, chain: str) -> Optional[Signal]:
        try:
            current_price = self.trading_client.get_token_price(token_address, chain)
            
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append({
                'price': current_price,
                'timestamp': time.time()
            })
            
            # Keep only recent prices
            cutoff_time = time.time() - (self.lookback_period * 3600)
            self.price_history[symbol] = [
                p for p in self.price_history[symbol] 
                if p['timestamp'] > cutoff_time
            ]
            
            if len(self.price_history[symbol]) < 10:  # Need enough data for statistics
                return None
            
            prices = np.array([p['price'] for p in self.price_history[symbol]])
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            if std_price == 0:
                return None
            
            z_score = (current_price - mean_price) / std_price
            
            if z_score > self.z_score_threshold:
                return Signal(
                    action='sell',
                    symbol=symbol,
                    strength=min(abs(z_score) / self.z_score_threshold, 1.0),
                    reason=f"Price too high (Z-score: {z_score:.2f})",
                    timestamp=time.time()
                )
            elif z_score < -self.z_score_threshold:
                return Signal(
                    action='buy',
                    symbol=symbol,
                    strength=min(abs(z_score) / self.z_score_threshold, 1.0),
                    reason=f"Price too low (Z-score: {z_score:.2f})",
                    timestamp=time.time()
                )
            
            return Signal(
                action='hold',
                symbol=symbol,
                strength=0.0,
                reason=f"Price normal (Z-score: {z_score:.2f})",
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing mean reversion for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, signal: Signal, available_capital: float) -> float:
        base_position_size = available_capital * 0.05  # 5% of available capital
        position_size = base_position_size * signal.strength
        
        max_position = available_capital * Config.MAX_POSITION_SIZE
        return min(position_size, max_position)

class MultiStrategyManager:
    def __init__(self):
        self.strategies = [
            MomentumStrategy(),
            MeanReversionStrategy()
        ]
        self.trading_client = RecallTradingClient()
        
    def generate_combined_signals(self) -> List[Signal]:
        all_signals = []
        
        for strategy in self.strategies:
            try:
                signals = strategy.generate_signals()
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Error getting signals from {strategy.__class__.__name__}: {e}")
        
        # Combine signals by symbol
        combined_signals = self._combine_signals_by_symbol(all_signals)
        return combined_signals
    
    def _combine_signals_by_symbol(self, signals: List[Signal]) -> List[Signal]:
        signal_groups = {}
        
        for signal in signals:
            if signal.symbol not in signal_groups:
                signal_groups[signal.symbol] = []
            signal_groups[signal.symbol].append(signal)
        
        combined_signals = []
        
        for symbol, symbol_signals in signal_groups.items():
            if len(symbol_signals) == 1:
                combined_signals.append(symbol_signals[0])
            else:
                # Combine multiple signals for the same symbol
                combined_signal = self._combine_signals(symbol_signals)
                combined_signals.append(combined_signal)
        
        return combined_signals
    
    def _combine_signals(self, signals: List[Signal]) -> Signal:
        buy_signals = [s for s in signals if s.action == 'buy']
        sell_signals = [s for s in signals if s.action == 'sell']
        
        buy_strength = sum(s.strength for s in buy_signals)
        sell_strength = sum(s.strength for s in sell_signals)
        
        if buy_strength > sell_strength:
            return Signal(
                action='buy',
                symbol=signals[0].symbol,
                strength=buy_strength - sell_strength,
                reason=f"Combined buy signals: {len(buy_signals)} buy, {len(sell_signals)} sell",
                timestamp=time.time()
            )
        elif sell_strength > buy_strength:
            return Signal(
                action='sell',
                symbol=signals[0].symbol,
                strength=sell_strength - buy_strength,
                reason=f"Combined sell signals: {len(sell_signals)} sell, {len(buy_signals)} buy",
                timestamp=time.time()
            )
        else:
            return Signal(
                action='hold',
                symbol=signals[0].symbol,
                strength=0.0,
                reason="Conflicting signals",
                timestamp=time.time()
            )