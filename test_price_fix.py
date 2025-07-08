#!/usr/bin/env python3
"""
Test script to verify price fetching fixes
"""

import sys
sys.path.append('src')

from src.trading_client import RecallTradingClient
from src.token_config import TokenConfigManager
from src.market_data import PriceMonitor, MarketDataProvider
import time

def test_price_fetching():
    """Test price fetching for all configured tokens"""
    print("🔍 Testing Price Fetching for All Tokens")
    print("=" * 50)
    
    # Initialize components
    trading_client = RecallTradingClient()
    token_config = TokenConfigManager()
    market_data = MarketDataProvider()
    
    # Get all enabled tokens
    tokens = token_config.get_enabled_tokens()
    
    successful_prices = 0
    failed_prices = 0
    
    print(f"Testing {len(tokens)} tokens:")
    print("-" * 30)
    
    for token in tokens:
        try:
            # Test direct API call
            print(f"🔄 Testing {token.symbol} ({token.chain})...")
            
            # Method 1: Direct trading client call
            price1 = trading_client.get_token_price(token.address, token.chain)
            
            # Method 2: Market data provider call
            price2 = market_data.get_current_price_by_symbol(token.symbol)
            
            if price1 is not None and price1 > 0:
                print(f"  ✅ Direct API: ${price1:.6f}")
                successful_prices += 1
            else:
                print(f"  ❌ Direct API: {price1}")
                failed_prices += 1
            
            if price2 is not None and price2 > 0:
                print(f"  ✅ Market Data: ${price2:.6f}")
            else:
                print(f"  ❌ Market Data: {price2}")
            
            # Check consistency
            if price1 and price2 and abs(price1 - price2) > 0.0001:
                print(f"  ⚠️  Price mismatch: {price1:.6f} vs {price2:.6f}")
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"  💥 Error testing {token.symbol}: {e}")
            failed_prices += 1
    
    print("-" * 30)
    print(f"📊 Results: {successful_prices} successful, {failed_prices} failed")
    
    return successful_prices, failed_prices

def test_price_monitor():
    """Test the price monitor functionality"""
    print("\n🎯 Testing Price Monitor")
    print("=" * 30)
    
    try:
        token_config = TokenConfigManager()
        symbols = token_config.get_token_symbols()
        
        # Initialize price monitor
        price_monitor = PriceMonitor(price_change_threshold=0.01)  # 1% threshold
        
        print(f"Monitoring {len(symbols)} symbols...")
        
        # First run to establish baseline
        alerts1 = price_monitor.monitor_prices(symbols)
        print(f"First run alerts: {len(alerts1)}")
        
        time.sleep(1)
        
        # Second run to check for changes
        alerts2 = price_monitor.monitor_prices(symbols)
        print(f"Second run alerts: {len(alerts2)}")
        
        # Display price status
        print("\n📈 Current Prices:")
        for symbol in symbols:
            if symbol in price_monitor.last_prices:
                price = price_monitor.last_prices[symbol]
                status = "✅" if price and price > 0 else "❌"
                print(f"  {status} {symbol}: ${price:.6f}" if price else f"  {status} {symbol}: None")
        
        return True
        
    except Exception as e:
        print(f"❌ Price monitor test failed: {e}")
        return False

def test_division_by_zero_fix():
    """Test that division by zero is properly handled"""
    print("\n🛡️  Testing Division by Zero Protection")
    print("=" * 40)
    
    try:
        price_monitor = PriceMonitor()
        
        # Simulate scenario that caused the original error
        price_monitor.last_prices = {
            'TEST_TOKEN': 0.0,  # This would cause division by zero
            'TEST_TOKEN2': None,  # This would also cause issues
        }
        
        # This should not crash now
        alerts = price_monitor.monitor_prices(['TEST_TOKEN', 'TEST_TOKEN2'])
        print(f"✅ Division by zero protection works: {len(alerts)} alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ Division by zero test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Price Fetching Tests\n")
    
    # Test 1: Price fetching
    successful, failed = test_price_fetching()
    
    # Test 2: Price monitor
    monitor_success = test_price_monitor()
    
    # Test 3: Division by zero protection
    div_zero_success = test_division_by_zero_fix()
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    print(f"Price Fetching: {successful} successful, {failed} failed")
    print(f"Price Monitor: {'✅ PASS' if monitor_success else '❌ FAIL'}")
    print(f"Division by Zero Protection: {'✅ PASS' if div_zero_success else '❌ FAIL'}")
    
    if failed == 0 and monitor_success and div_zero_success:
        print("\n🎉 All tests passed! Price fetching issues should be resolved.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some issues remain. Check the API endpoints for failed tokens.")
        sys.exit(1)