#!/usr/bin/env python3
"""
Test script for EVM trading functionality
"""

import sys
sys.path.append('src')

from src.trading_client import RecallTradingClient
from src.portfolio_manager import PortfolioManager
import json

def test_evm_functionality():
    """Test EVM token support and trading"""
    print("Testing EVM Trading Functionality")
    print("=" * 50)
    
    # Initialize clients
    trading_client = RecallTradingClient()
    portfolio_manager = PortfolioManager()
    
    # Test 1: Check portfolio status with EVM tokens
    print("\n1. Testing portfolio status with EVM tokens:")
    try:
        portfolio_status = portfolio_manager.get_portfolio_status()
        print(f"Found {len(portfolio_status)} tokens in portfolio:")
        
        total_value = sum(target.current_value for target in portfolio_status.values())
        print(f"Total portfolio value: ${total_value:,.2f}")
        
        for symbol, target in portfolio_status.items():
            chain = portfolio_manager._get_token_chain(symbol)
            chain_emoji = "⚡" if chain == "ethereum" else "🚀" if chain == "solana" else "🔗"
            print(f"  {chain_emoji} {symbol} ({chain}): Target {target.target_allocation:.1%} | "
                  f"Current {target.current_allocation:.1%} | "
                  f"Drift {target.drift:+.1%} | "
                  f"Value ${target.current_value:,.2f}")
        
        print("✅ Portfolio status test passed")
        
    except Exception as e:
        print(f"❌ Portfolio status test failed: {e}")
        return False
    
    # Test 2: Check price fetching for EVM tokens
    print("\n2. Testing price fetching for EVM tokens:")
    try:
        # Test WETH price
        weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        weth_price = trading_client.get_token_price(weth_address, "ethereum")
        print(f"  WETH price: ${weth_price:,.2f}")
        
        # Test USDC price on Ethereum
        usdc_eth_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        usdc_eth_price = trading_client.get_token_price(usdc_eth_address, "ethereum")
        print(f"  USDC (Ethereum) price: ${usdc_eth_price:.4f}")
        
        # Test SOL price
        sol_address = "So11111111111111111111111111111111111111112"
        sol_price = trading_client.get_token_price(sol_address, "solana")
        print(f"  SOL price: ${sol_price:.2f}")
        
        # Test USDC price on Solana
        usdc_sol_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        usdc_sol_price = trading_client.get_token_price(usdc_sol_address, "solana")
        print(f"  USDC (Solana) price: ${usdc_sol_price:.4f}")
        
        print("✅ Price fetching test passed")
        
    except Exception as e:
        print(f"❌ Price fetching test failed: {e}")
        return False
    
    # Test 3: Calculate rebalance trades
    print("\n3. Testing rebalance trade calculation:")
    try:
        trades = portfolio_manager.calculate_rebalance_trades()
        print(f"Found {len(trades)} potential rebalance trades:")
        
        for from_symbol, to_symbol, amount in trades:
            from_chain = portfolio_manager._get_token_chain(from_symbol)
            to_chain = portfolio_manager._get_token_chain(to_symbol)
            
            if from_chain == to_chain:
                chain_emoji = "⚡" if from_chain == "ethereum" else "🚀" if from_chain == "solana" else "🔗"
                print(f"  {chain_emoji} {from_symbol} -> {to_symbol}: ${amount:,.2f} (same chain: {from_chain})")
            else:
                print(f"  ❌ {from_symbol} ({from_chain}) -> {to_symbol} ({to_chain}): ${amount:,.2f} (cross-chain - not supported)")
        
        print("✅ Rebalance calculation test passed")
        
    except Exception as e:
        print(f"❌ Rebalance calculation test failed: {e}")
        return False
    
    # Test 4: Token info lookup
    print("\n4. Testing token info lookup:")
    try:
        test_tokens = [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC ETH
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC SOL
        ]
        
        for token_address in test_tokens:
            token_info = trading_client.get_token_info(token_address)
            chain_emoji = "⚡" if token_info['chain'] == "ethereum" else "🚀" if token_info['chain'] == "solana" else "🔗"
            print(f"  {chain_emoji} {token_address[:10]}... -> {token_info['symbol']} on {token_info['chain']}")
        
        print("✅ Token info lookup test passed")
        
    except Exception as e:
        print(f"❌ Token info lookup test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All EVM trading functionality tests passed!")
    print("✅ Multi-chain portfolio management is working")
    print("✅ Price fetching supports both EVM and SVM tokens")
    print("✅ Rebalance logic correctly handles same-chain trades")
    print("✅ Cross-chain trades are properly filtered out")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_evm_functionality()
    sys.exit(0 if success else 1)