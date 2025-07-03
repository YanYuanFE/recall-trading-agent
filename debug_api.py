#!/usr/bin/env python3
"""
Debug script for Recall API connectivity
"""

import requests
import sys
import os
sys.path.append('src')

from src.config import Config

def test_api_endpoints():
    """Test various API endpoints to determine the correct format"""
    
    api_key = Config.TRADING_SIM_API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    base_urls = [
        "https://api.competitions.recall.network",
        "https://api.competitions.recall.network/api", 
        "https://api.competitions.recall.network/sandbox",
        "https://api.competitions.recall.network/sandbox/api"
    ]
    
    endpoints = [
        "/health",
        "/account/portfolio", 
        "/account/balances",
        "/account/positions",
        "/account/history",
        "/account/trades",
        "/agent/portfolio", 
        "/agent/balances",
        "/agent/history",
        "/agent/trades",
        "/competition/status",
        "/competition/leaderboard",
        "/competition/info",
        "/trade/quote",
        "/trade/execute",
        "/market/tokens",
        "/market/price",
        "/market/prices"
    ]
    
    print(f"Testing API Key: {api_key[:10]}...")
    print("=" * 80)
    
    # First test health endpoint without auth
    print("1. Testing health endpoints (no auth required):")
    for base_url in base_urls:
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            print(f"   {base_url}/health -> {response.status_code}")
            if response.status_code == 200:
                print(f"      Response: {response.json()}")
        except Exception as e:
            print(f"   {base_url}/health -> ERROR: {e}")
    
    print("\n2. Testing authenticated endpoints:")
    for base_url in base_urls:
        for endpoint in endpoints[1:]:  # Skip health
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, headers=headers, timeout=10)
                print(f"   {url} -> {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"      SUCCESS: {data}")
                    except:
                        print(f"      SUCCESS: {response.text[:100]}...")
                elif response.status_code in [401, 403]:
                    try:
                        error = response.json()
                        print(f"      AUTH ERROR: {error}")
                    except:
                        print(f"      AUTH ERROR: {response.text[:100]}...")
                elif response.status_code == 404:
                    print(f"      NOT FOUND")
                else:
                    print(f"      ERROR: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   {url} -> EXCEPTION: {e}")
    
    print("\n3. Testing trade execution endpoint:")
    # Test the known working endpoint from documentation
    trade_url = "https://api.competitions.recall.network/sandbox/api/trade/execute"
    
    # Simple test payload
    payload = {
        "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH  
        "amount": "1",
        "reason": "API test trade"
    }
    
    try:
        response = requests.post(trade_url, json=payload, headers=headers, timeout=10)
        print(f"   {trade_url} -> {response.status_code}")
        try:
            data = response.json()
            print(f"      Response: {data}")
        except:
            print(f"      Response: {response.text}")
    except Exception as e:
        print(f"   {trade_url} -> EXCEPTION: {e}")

if __name__ == "__main__":
    test_api_endpoints()