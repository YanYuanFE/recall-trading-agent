#!/usr/bin/env python3
"""
Test Recall API trading functionality with custom API key
"""

import requests
import sys
import json

def test_recall_trade(api_key):
    """Test the Recall trading API with the provided key"""
    
    url = "https://api.competitions.recall.network/sandbox/api/trade/execute"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "amount": "100",
        "reason": "Trading 100 USDC to WETH on Ethereum Mainnet to verify Recall developer account"
    }
    
    print(f"Testing API Key: {api_key[:10]}...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200 and response_data.get('success'):
                print("✅ Trade executed successfully!")
                return True
            else:
                print("❌ Trade failed!")
                return False
                
        except json.JSONDecodeError:
            print(f"Raw Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_other_endpoints(api_key):
    """Test other API endpoints"""
    
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {api_key}"
    }
    
    base_url = "https://api.competitions.recall.network/sandbox/api"
    
    endpoints = [
        "/account/balances",
        "/account/portfolio", 
        "/competition/status"
    ]
    
    print("\nTesting other endpoints:")
    print("=" * 40)
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"{endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  ✅ Success: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  ✅ Success: {response.text[:100]}...")
            else:
                try:
                    error = response.json()
                    print(f"  ❌ Error: {error.get('error', 'Unknown error')}")
                except:
                    print(f"  ❌ Error: {response.text[:100]}")
                    
        except Exception as e:
            print(f"{endpoint}: ❌ Exception: {e}")

if __name__ == "__main__":
    # You can pass the API key as a command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        # Or use the one from the .env file
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("TRADING_SIM_API_KEY", "")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ No valid API key provided!")
        print("Usage: python3 test_trade.py <your-api-key>")
        print("   or: Update the .env file with your API key")
        sys.exit(1)
    
    print("🚀 Testing Recall API Trading...")
    print("=" * 60)
    
    # Test trade execution
    trade_success = test_recall_trade(api_key)
    
    # Test other endpoints
    test_other_endpoints(api_key)
    
    print("\n" + "=" * 60)
    if trade_success:
        print("🎉 All tests passed! Your API key is working correctly.")
    else:
        print("⚠️  API key validation failed. Please check:")
        print("   1. API key is correct and not expired")
        print("   2. Account is properly registered")
        print("   3. Team is created and verified")
        print("   4. Account has sufficient sandbox balance")