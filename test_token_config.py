#!/usr/bin/env python3
"""
Test script for the new token configuration system
"""

import sys
sys.path.append('src')

from src.token_config import TokenConfigManager
from src.trading_strategy import MultiStrategyManager
import json

def test_token_configuration():
    """Test the token configuration system"""
    print("🔧 Testing Token Configuration System")
    print("=" * 60)
    
    # Initialize token config manager
    try:
        token_config = TokenConfigManager()
        print("✅ Token configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load token configuration: {e}")
        return False
    
    # Test 1: Display token summary
    print("\n📊 Token Summary:")
    print(token_config.get_token_summary())
    
    # Test 2: Check enabled tokens
    enabled_tokens = token_config.get_enabled_tokens()
    print(f"\n📈 Enabled tokens: {len(enabled_tokens)}")
    for token in enabled_tokens:
        volatility_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "very_high": "🔴"}.get(token.volatility_expected, "⚪")
        print(f"  {volatility_emoji} {token.symbol} ({token.chain}): {token.category} - {token.volatility_expected} volatility")
    
    # Test 3: Check strategy thresholds
    print(f"\n⚙️  Strategy Configuration:")
    strategy_config = token_config.get_strategy_config()
    
    print("  Momentum Thresholds:")
    for category, threshold in strategy_config['momentum_strategy']['thresholds'].items():
        print(f"    {category}: {threshold:.1%}")
    
    print("  Mean Reversion Z-Score Thresholds:")
    for category, threshold in strategy_config['mean_reversion_strategy']['z_score_thresholds'].items():
        print(f"    {category}: {threshold:.1f}")
    
    # Test 4: Check meme tokens (should have higher thresholds)
    print(f"\n🐸 Meme Tokens Analysis:")
    meme_tokens = token_config.get_tokens_by_category('meme')
    for token in meme_tokens:
        momentum_threshold = token.get_momentum_threshold(strategy_config)
        z_score_threshold = token.get_z_score_threshold(strategy_config)
        volatility_mult = token.get_volatility_multiplier(token_config.get_risk_config())
        adjusted_momentum = momentum_threshold * volatility_mult
        
        print(f"  🎭 {token.symbol}: momentum {adjusted_momentum:.1%}, z-score ±{z_score_threshold:.1f}")
    
    # Test 5: Test strategy manager initialization
    print(f"\n🤖 Strategy Manager Test:")
    try:
        strategy_manager = MultiStrategyManager()
        print("✅ Multi-strategy manager initialized successfully")
        
        # Test signal generation (dry run)
        print("📡 Testing signal generation...")
        signals = strategy_manager.generate_combined_signals()
        print(f"📊 Generated {len(signals)} trading signals")
        
        for signal in signals:
            action_emoji = {"buy": "📈", "sell": "📉", "hold": "⏸️"}.get(signal.action, "❓")
            print(f"  {action_emoji} {signal.symbol}: {signal.action} (strength: {signal.strength:.2f}) - {signal.reason}")
    
    except Exception as e:
        print(f"❌ Strategy manager test failed: {e}")
        return False
    
    # Test 6: Risk management validation
    print(f"\n🛡️  Risk Management Test:")
    risk_config = token_config.get_risk_config()
    
    # Simulate high meme allocation
    test_allocations = {
        "PEPE": 0.15,
        "SHIB": 0.10,
        "BONK": 0.08,
        "SOL": 0.30,
        "WETH": 0.37
    }
    
    is_valid = token_config.validate_token_allocation(test_allocations)
    print(f"Test allocation validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test 7: Trading pairs configuration
    print(f"\n🔄 Trading Pairs Configuration:")
    trading_pairs = token_config.get_trading_pairs_config()
    for chain, tokens in trading_pairs.items():
        print(f"  {chain.upper()}: {len(tokens)} tokens")
        for symbol, address in tokens.items():
            print(f"    {symbol}: {address[:10]}...{address[-6:]}")
    
    print("\n" + "=" * 60)
    print("🎉 Token Configuration System Test Complete!")
    print(f"✅ {len(enabled_tokens)} tokens configured across {len(trading_pairs)} chains")
    print(f"📊 Strategies configured with dynamic thresholds based on token categories")
    print(f"🛡️  Risk management rules in place for portfolio allocation")
    print("=" * 60)
    
    return True

def test_signal_generation_details():
    """Test detailed signal generation with new token configuration"""
    print("\n🔍 Detailed Signal Generation Test")
    print("-" * 40)
    
    try:
        token_config = TokenConfigManager()
        strategy_manager = MultiStrategyManager()
        
        # Test each strategy individually
        for i, strategy in enumerate(strategy_manager.strategies):
            strategy_name = strategy.__class__.__name__
            print(f"\n📈 Testing {strategy_name}:")
            
            signals = strategy.generate_signals()
            print(f"Generated {len(signals)} signals from {strategy_name}")
            
            for signal in signals:
                print(f"  • {signal.symbol}: {signal.action} (strength: {signal.strength:.3f})")
                print(f"    Reason: {signal.reason}")
        
        print(f"\n🔄 Combined Strategy Results:")
        combined_signals = strategy_manager.generate_combined_signals()
        print(f"Final combined signals: {len(combined_signals)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Token Configuration Tests\n")
    
    success1 = test_token_configuration()
    success2 = test_signal_generation_details()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The token configuration system is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1)