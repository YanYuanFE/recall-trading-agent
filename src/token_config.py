#!/usr/bin/env python3
"""
Token Configuration Manager
Manages trading tokens configuration and provides utilities for token-based trading.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    symbol: str
    address: str
    chain: str
    decimals: int
    category: str
    enabled: bool
    volatility_expected: str
    
    def get_momentum_threshold(self, strategy_config: Dict) -> float:
        """Get momentum threshold based on token category"""
        thresholds = strategy_config.get('momentum_strategy', {}).get('thresholds', {})
        return thresholds.get(self.category, thresholds.get('default', 0.05))
    
    def get_z_score_threshold(self, strategy_config: Dict) -> float:
        """Get Z-score threshold based on token category"""
        thresholds = strategy_config.get('mean_reversion_strategy', {}).get('z_score_thresholds', {})
        return thresholds.get(self.category, thresholds.get('default', 2.0))
    
    def get_position_size_ratio(self, strategy_config: Dict) -> float:
        """Get position size ratio based on token category"""
        ratios = strategy_config.get('position_sizing', {})
        return ratios.get(self.category, ratios.get('default', 0.10))
    
    def get_volatility_multiplier(self, risk_config: Dict) -> float:
        """Get volatility multiplier based on expected volatility"""
        multipliers = risk_config.get('volatility_multipliers', {})
        return multipliers.get(self.volatility_expected, 1.0)

class TokenConfigManager:
    def __init__(self, config_path: str = "config/trading_tokens.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.tokens = self._parse_tokens()
    
    def _load_config(self) -> Dict:
        """Load token configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded token configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Token config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in token config file: {e}")
            raise
    
    def _parse_tokens(self) -> Dict[str, TokenInfo]:
        """Parse tokens from configuration"""
        tokens = {}
        
        for chain, chain_tokens in self.config.get('trading_tokens', {}).items():
            for symbol, token_data in chain_tokens.items():
                token_info = TokenInfo(
                    symbol=symbol,
                    address=token_data['address'],
                    chain=chain,
                    decimals=token_data['decimals'],
                    category=token_data['category'],
                    enabled=token_data.get('enabled', True),
                    volatility_expected=token_data.get('volatility_expected', 'medium')
                )
                
                # Use chain_symbol as key to handle same symbols on different chains
                key = f"{symbol}_{chain}" if self._has_duplicate_symbols(symbol) else symbol
                tokens[key] = token_info
        
        return tokens
    
    def _has_duplicate_symbols(self, symbol: str) -> bool:
        """Check if symbol exists on multiple chains"""
        count = 0
        for chain_tokens in self.config.get('trading_tokens', {}).values():
            if symbol in chain_tokens:
                count += 1
        return count > 1
    
    def get_all_tokens(self) -> List[TokenInfo]:
        """Get all configured tokens"""
        return list(self.tokens.values())
    
    def get_enabled_tokens(self) -> List[TokenInfo]:
        """Get only enabled tokens"""
        return [token for token in self.tokens.values() if token.enabled]
    
    def get_tokens_by_chain(self, chain: str) -> List[TokenInfo]:
        """Get tokens for a specific chain"""
        return [token for token in self.tokens.values() if token.chain == chain and token.enabled]
    
    def get_tokens_by_category(self, category: str) -> List[TokenInfo]:
        """Get tokens by category (e.g., 'meme', 'defi', 'major')"""
        return [token for token in self.tokens.values() if token.category == category and token.enabled]
    
    def get_token_by_symbol(self, symbol: str, chain: Optional[str] = None) -> Optional[TokenInfo]:
        """Get token by symbol, optionally filtered by chain"""
        if chain:
            key = f"{symbol}_{chain}" if self._has_duplicate_symbols(symbol) else symbol
            return self.tokens.get(key)
        else:
            # Return first match if no chain specified
            for token in self.tokens.values():
                if token.symbol == symbol:
                    return token
            return None
    
    def get_token_by_address(self, address: str) -> Optional[TokenInfo]:
        """Get token by contract address"""
        for token in self.tokens.values():
            if token.address.lower() == address.lower():
                return token
        return None
    
    def get_strategy_config(self) -> Dict:
        """Get strategy configuration"""
        return self.config.get('strategy_config', {})
    
    def get_risk_config(self) -> Dict:
        """Get risk management configuration"""
        return self.config.get('risk_management', {})
    
    def get_non_stablecoin_tokens(self) -> List[TokenInfo]:
        """Get all non-stablecoin tokens for trading signals"""
        return [token for token in self.tokens.values() 
                if token.enabled and token.category != 'stablecoin']
    
    def get_high_volatility_tokens(self) -> List[TokenInfo]:
        """Get tokens with high or very high expected volatility"""
        return [token for token in self.tokens.values() 
                if token.enabled and token.volatility_expected in ['high', 'very_high']]
    
    def is_meme_token(self, symbol: str) -> bool:
        """Check if token is a meme token"""
        token = self.get_token_by_symbol(symbol)
        return token is not None and token.category == 'meme'
    
    def get_token_symbols(self) -> List[str]:
        """Get list of all enabled token symbols"""
        return [token.symbol for token in self.get_enabled_tokens()]
    
    def validate_token_allocation(self, allocations: Dict[str, float]) -> bool:
        """Validate if token allocations comply with risk management rules"""
        risk_config = self.get_risk_config()
        
        # Check maximum meme allocation
        max_meme_allocation = risk_config.get('max_meme_allocation', 0.20)
        meme_allocation = sum(
            allocation for symbol, allocation in allocations.items() 
            if self.is_meme_token(symbol)
        )
        
        if meme_allocation > max_meme_allocation:
            logger.warning(f"Meme token allocation {meme_allocation:.1%} exceeds limit {max_meme_allocation:.1%}")
            return False
        
        # Check maximum single token allocation
        max_single_allocation = risk_config.get('max_single_token_allocation', 0.30)
        for symbol, allocation in allocations.items():
            if allocation > max_single_allocation:
                logger.warning(f"Token {symbol} allocation {allocation:.1%} exceeds limit {max_single_allocation:.1%}")
                return False
        
        return True
    
    def get_trading_pairs_config(self) -> Dict[str, Dict[str, str]]:
        """Get trading pairs configuration for portfolio manager"""
        trading_pairs = {}
        
        for token in self.get_enabled_tokens():
            if token.chain not in trading_pairs:
                trading_pairs[token.chain] = {}
            trading_pairs[token.chain][token.symbol] = token.address
        
        return trading_pairs
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self.tokens = self._parse_tokens()
        logger.info("Token configuration reloaded")
    
    def get_token_summary(self) -> str:
        """Get a summary of configured tokens"""
        enabled_tokens = self.get_enabled_tokens()
        
        summary = [
            f"Total Tokens: {len(enabled_tokens)}",
            f"Chains: {len(set(token.chain for token in enabled_tokens))}",
            ""
        ]
        
        # Group by chain
        for chain in set(token.chain for token in enabled_tokens):
            chain_tokens = self.get_tokens_by_chain(chain)
            summary.append(f"{chain.upper()} ({len(chain_tokens)} tokens):")
            
            # Group by category
            categories = {}
            for token in chain_tokens:
                if token.category not in categories:
                    categories[token.category] = []
                categories[token.category].append(token.symbol)
            
            for category, symbols in categories.items():
                volatility_info = {token.volatility_expected for token in chain_tokens if token.symbol in symbols}
                summary.append(f"  {category}: {', '.join(symbols)} ({', '.join(volatility_info)} volatility)")
            
            summary.append("")
        
        return "\n".join(summary)