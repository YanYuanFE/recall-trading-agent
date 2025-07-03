#!/usr/bin/env python3
"""
Comprehensive Recall Account and API Diagnostics
"""

import requests
import sys
import json

def check_api_key_format(api_key):
    """Check if API key follows expected format"""
    print("🔍 API Key Format Analysis:")
    print(f"   Length: {len(api_key)}")
    print(f"   Contains underscore: {'_' in api_key}")
    print(f"   Format: {'hex_hex' if '_' in api_key and all(c in '0123456789abcdef_' for c in api_key.lower()) else 'unknown'}")
    
    if len(api_key) != 33 or '_' not in api_key:
        print("   ⚠️  Warning: API key format may be incorrect")
        print("      Expected format: 16chars_16chars (33 total with underscore)")
    else:
        print("   ✅ API key format looks correct")
    print()

def test_public_endpoints():
    """Test public endpoints to verify API connectivity"""
    print("🌐 Testing Public Endpoints:")
    
    public_endpoints = [
        "https://api.competitions.recall.network/health",
        "https://api.competitions.recall.network/api/health", 
        "https://api.competitions.recall.network/sandbox/api/health"
    ]
    
    for endpoint in public_endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {endpoint} -> OK")
                print(f"      {data}")
            else:
                print(f"   ❌ {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} -> ERROR: {e}")
    print()

def test_auth_with_different_urls(api_key):
    """Test authentication with different API base URLs"""
    print("🔐 Testing Authentication with Different API URLs:")
    
    base_urls = [
        "https://api.competitions.recall.network/api",
        "https://api.competitions.recall.network/sandbox/api", 
        "https://api.competitions.recall.network",
        "https://api.competitions.recall.network/sandbox"
    ]
    
    test_endpoint = "/account/portfolio"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for base_url in base_urls:
        try:
            url = f"{base_url}{test_endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"   {url}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - API key is valid!")
                try:
                    data = response.json()
                    print(f"   Data: {json.dumps(data, indent=6)}")
                except:
                    print(f"   Raw response: {response.text}")
                return True
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"   ❌ AUTH FAILED: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   ❌ AUTH FAILED: {response.text}")
            elif response.status_code == 404:
                print("   ❌ ENDPOINT NOT FOUND")
            else:
                print(f"   ❌ UNEXPECTED ERROR: {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Raw: {response.text}")
            print()
            
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            print()
    
    return False

def test_minimal_trade(api_key):
    """Test with minimal trade amount"""
    print("💱 Testing Minimal Trade:")
    
    url = "https://api.competitions.recall.network/sandbox/api/trade/execute"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try with minimal amount
    payload = {
        "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "amount": "1",  # Minimal amount
        "reason": "Minimal test trade for API verification"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=6)}")
            
            if response.status_code == 200 and data.get('success'):
                print("   ✅ Trade successful!")
                return True
            else:
                print("   ❌ Trade failed")
                return False
        except:
            print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("TRADING_SIM_API_KEY", "")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ No API key provided!")
        print("Usage: python3 diagnose_account.py <api-key>")
        sys.exit(1)
    
    print("🔬 RECALL ACCOUNT DIAGNOSTICS")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print("=" * 60)
    print()
    
    # Run diagnostics
    check_api_key_format(api_key)
    test_public_endpoints()
    auth_success = test_auth_with_different_urls(api_key)
    
    if not auth_success:
        print("📋 TROUBLESHOOTING STEPS:")
        print("=" * 60)
        print("1. Verify account registration:")
        print("   - Visit https://register.recall.network")
        print("   - Ensure account is fully verified")
        print("   - Check email for verification links")
        print()
        print("2. Complete team registration:")
        print("   - Create team with 3-30 character name")
        print("   - Add team description")
        print("   - Ensure team is approved")
        print()
        print("3. Register for competition:")
        print("   - Join '7 Day Trading Challenge' or active competition")
        print("   - Wait for registration approval")
        print()
        print("4. Generate new API key:")
        print("   - Go to team settings")
        print("   - Generate fresh API key")
        print("   - Ensure you copy the complete key")
        print()
        print("5. Check account status:")
        print("   - Verify sandbox access is enabled")
        print("   - Check if account has any restrictions")
        print()
    else:
        print("🎉 SUCCESS! Your API key is working correctly.")
        print("You can now run the trading agent!")
        
        # Test a minimal trade if auth works
        test_minimal_trade(api_key)

if __name__ == "__main__":
    main()