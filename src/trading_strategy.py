import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from src.trading_client import RecallTradingClient
from src.config import Config
from src.token_config import TokenConfigManager

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
    def __init__(self, token_config_manager: Optional[TokenConfigManager] = None):
        super().__init__()
        self.token_config = token_config_manager or TokenConfigManager()
        self.strategy_config = self.token_config.get_strategy_config()
        self.momentum_config = self.strategy_config.get('momentum_strategy', {})
        self.lookback_period = self.momentum_config.get('lookback_hours', 12)
        self.price_history = {}
        
    def generate_signals(self) -> List[Signal]:
        signals = []
        
        try:
            # Get non-stablecoin tokens from configuration
            tradeable_tokens = self.token_config.get_non_stablecoin_tokens()
            
            logger.info(f"Analyzing momentum for {len(tradeable_tokens)} tokens")
            
            for token in tradeable_tokens:
                signal = self._analyze_momentum(token)
                if signal and signal.action != 'hold':  # Only include actionable signals
                    signals.append(signal)
                    logger.info(f"Generated {signal.action} signal for {token.symbol}: {signal.reason}")
                    
        except Exception as e:
            logger.error(f"Error generating momentum signals: {e}")
            
        return signals
    
    def _analyze_momentum(self, token) -> Optional[Signal]:
        try:
            # Get current price
            current_price = self.trading_client.get_token_price(token.address, token.chain)
            
            if current_price is None or current_price <= 0:
                logger.debug(f"Cannot get valid price for {token.symbol}: {current_price}")
                return None
            
            # Get token-specific momentum threshold
            momentum_threshold = token.get_momentum_threshold(self.strategy_config)
            volatility_multiplier = token.get_volatility_multiplier(self.token_config.get_risk_config())
            
            # Adjust threshold based on volatility
            adjusted_threshold = momentum_threshold * volatility_multiplier
            
            # Store price history
            symbol_key = f"{token.symbol}_{token.chain}"
            if symbol_key not in self.price_history:
                self.price_history[symbol_key] = []
            
            self.price_history[symbol_key].append({
                'price': current_price,
                'timestamp': time.time()
            })
            
            # Keep only recent prices
            cutoff_time = time.time() - (self.lookback_period * 3600)
            self.price_history[symbol_key] = [
                p for p in self.price_history[symbol_key] 
                if p['timestamp'] > cutoff_time
            ]
            
            if len(self.price_history[symbol_key]) < 2:
                logger.debug(f"Insufficient price history for {token.symbol}")
                return None
            
            # Calculate momentum
            prices = [p['price'] for p in self.price_history[symbol_key]]
            recent_return = (prices[-1] - prices[0]) / prices[0]
            
            logger.debug(f"{token.symbol}: price change {recent_return:.2%}, threshold ±{adjusted_threshold:.2%}")
            
            if recent_return > adjusted_threshold:
                strength = min(abs(recent_return) / adjusted_threshold, 1.0)
                return Signal(
                    action='buy',
                    symbol=token.symbol,
                    strength=strength,
                    reason=f"Positive momentum: {recent_return:.2%} (threshold: {adjusted_threshold:.2%})",
                    timestamp=time.time()
                )
            elif recent_return < -adjusted_threshold:
                strength = min(abs(recent_return) / adjusted_threshold, 1.0)
                return Signal(
                    action='sell',
                    symbol=token.symbol,
                    strength=strength,
                    reason=f"Negative momentum: {recent_return:.2%} (threshold: {adjusted_threshold:.2%})",
                    timestamp=time.time()
                )
            
            return Signal(
                action='hold',
                symbol=token.symbol,
                strength=0.0,
                reason=f"No significant momentum: {recent_return:.2%}",
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing momentum for {token.symbol}: {e}")
            return None
    
    def calculate_position_size(self, signal: Signal, available_capital: float) -> float:
        # Get token-specific position sizing
        token = self.token_config.get_token_by_symbol(signal.symbol)
        if token:
            base_ratio = token.get_position_size_ratio(self.strategy_config)
        else:
            base_ratio = 0.1  # Default 10%
        
        # Position size based on signal strength and token category
        base_position_size = available_capital * base_ratio
        position_size = base_position_size * signal.strength
        
        # Apply maximum position size limit
        max_position = available_capital * Config.MAX_POSITION_SIZE
        return min(position_size, max_position)

class MeanReversionStrategy(TradingStrategy):
    def __init__(self, token_config_manager: Optional[TokenConfigManager] = None):
        super().__init__()
        self.token_config = token_config_manager or TokenConfigManager()
        self.strategy_config = self.token_config.get_strategy_config()
        self.reversion_config = self.strategy_config.get('mean_reversion_strategy', {})
        self.lookback_period = self.reversion_config.get('lookback_hours', 24)
        self.price_history = {}
        
    def generate_signals(self) -> List[Signal]:
        signals = []
        
        try:
            # Get non-stablecoin tokens from configuration
            tradeable_tokens = self.token_config.get_non_stablecoin_tokens()
            
            logger.info(f"Analyzing mean reversion for {len(tradeable_tokens)} tokens")
            
            for token in tradeable_tokens:
                signal = self._analyze_mean_reversion(token)
                if signal and signal.action != 'hold':  # Only include actionable signals
                    signals.append(signal)
                    logger.info(f"Generated {signal.action} signal for {token.symbol}: {signal.reason}")
                    
        except Exception as e:
            logger.error(f"Error generating mean reversion signals: {e}")
            
        return signals
    
    def _analyze_mean_reversion(self, token) -> Optional[Signal]:
        try:
            current_price = self.trading_client.get_token_price(token.address, token.chain)
            
            if current_price is None or current_price <= 0:
                logger.debug(f"Cannot get valid price for {token.symbol}: {current_price}")
                return None
            
            # Get token-specific z-score threshold
            z_score_threshold = token.get_z_score_threshold(self.strategy_config)
            
            symbol_key = f"{token.symbol}_{token.chain}"
            if symbol_key not in self.price_history:
                self.price_history[symbol_key] = []
            
            self.price_history[symbol_key].append({
                'price': current_price,
                'timestamp': time.time()
            })
            
            # Keep only recent prices
            cutoff_time = time.time() - (self.lookback_period * 3600)
            self.price_history[symbol_key] = [
                p for p in self.price_history[symbol_key] 
                if p['timestamp'] > cutoff_time
            ]
            
            if len(self.price_history[symbol_key]) < 10:  # Need enough data for statistics
                logger.debug(f"Insufficient price history for {token.symbol} mean reversion")
                return None
            
            prices = np.array([p['price'] for p in self.price_history[symbol_key]])
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            if std_price == 0:
                return None
            
            z_score = (current_price - mean_price) / std_price
            
            logger.debug(f"{token.symbol}: Z-score {z_score:.2f}, threshold ±{z_score_threshold:.2f}")
            
            if z_score > z_score_threshold:
                strength = min(abs(z_score) / z_score_threshold, 1.0)
                return Signal(
                    action='sell',
                    symbol=token.symbol,
                    strength=strength,
                    reason=f"Price too high (Z-score: {z_score:.2f}, threshold: {z_score_threshold:.2f})",
                    timestamp=time.time()
                )
            elif z_score < -z_score_threshold:
                strength = min(abs(z_score) / z_score_threshold, 1.0)
                return Signal(
                    action='buy',
                    symbol=token.symbol,
                    strength=strength,
                    reason=f"Price too low (Z-score: {z_score:.2f}, threshold: {z_score_threshold:.2f})",
                    timestamp=time.time()
                )
            
            return Signal(
                action='hold',
                symbol=token.symbol,
                strength=0.0,
                reason=f"Price normal (Z-score: {z_score:.2f})",
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing mean reversion for {token.symbol}: {e}")
            return None
    
    def calculate_position_size(self, signal: Signal, available_capital: float) -> float:
        # Get token-specific position sizing (more conservative for mean reversion)
        token = self.token_config.get_token_by_symbol(signal.symbol)
        if token:
            base_ratio = token.get_position_size_ratio(self.strategy_config) * 0.5  # Half size for mean reversion
        else:
            base_ratio = 0.05  # Default 5%
        
        base_position_size = available_capital * base_ratio
        position_size = base_position_size * signal.strength
        
        max_position = available_capital * Config.MAX_POSITION_SIZE
        return min(position_size, max_position)

class MultiStrategyManager:
    def __init__(self):
        self.token_config = TokenConfigManager()
        self.strategies = [
            MomentumStrategy(self.token_config),
            MeanReversionStrategy(self.token_config)
        ]
        self.trading_client = RecallTradingClient()
        
        # Log configuration summary
        logger.info("Multi-Strategy Trading System Initialized")
        logger.info(self.token_config.get_token_summary())
        
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