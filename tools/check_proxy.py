#!/usr/bin/env python3
"""
Proxy verification tool for debugging proxy configuration.
Tests proxy connectivity using both requests library and Selenium.

This script helps verify:
1. Proxy credentials are correct
2. Proxy IP is being used (not your real IP)
3. Headers look realistic
4. Selenium-wire is properly configured

Usage:
    python tools/check_proxy.py

Environment variables needed (if using proxy):
    OXY_USERNAME - Oxylabs username
    OXY_PASSWORD - Oxylabs password  
    OXY_HOST - Oxylabs host (e.g., pr.oxylabs.io)
    OXY_PORT - Oxylabs port (e.g., 7777)
    OXY_STICKY - Optional sticky session ID
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_with_requests():
    """Check proxy using requests library."""
    import requests
    
    print("\n" + "="*60)
    print("TESTING WITH REQUESTS LIBRARY")
    print("="*60)
    
    oxy_username = os.getenv('OXY_USERNAME')
    oxy_password = os.getenv('OXY_PASSWORD')
    oxy_host = os.getenv('OXY_HOST', 'pr.oxylabs.io')
    oxy_port = os.getenv('OXY_PORT', '7777')
    oxy_sticky = os.getenv('OXY_STICKY', '')
    
    if not oxy_username or not oxy_password:
        print("⚠️  No proxy credentials found. Testing with direct connection...")
        proxies = None
    else:
        # Build username with optional sticky session
        if oxy_sticky:
            username = f"{oxy_username}-session-{oxy_sticky}"
            print(f"✅ Using sticky session: {oxy_sticky}")
        else:
            username = oxy_username
            print("ℹ️  No sticky session configured")
        
        proxy_url = f"http://{username}:{oxy_password}@{oxy_host}:{oxy_port}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url,
        }
        print(f"📍 Proxy: {oxy_host}:{oxy_port}")
        print(f"👤 Username: {username}")
    
    try:
        # Test 1: Get IP address
        print("\n[Test 1] Checking IP address...")
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=30)
        response.raise_for_status()
        ip_data = response.json()
        print(f"✅ Your IP: {ip_data.get('origin', 'unknown')}")
        
        # Test 2: Check headers
        print("\n[Test 2] Checking headers...")
        response = requests.get('https://httpbin.org/headers', proxies=proxies, timeout=30)
        response.raise_for_status()
        headers_data = response.json()
        headers = headers_data.get('headers', {})
        
        print(f"   User-Agent: {headers.get('User-Agent', 'N/A')}")
        print(f"   Accept-Language: {headers.get('Accept-Language', 'N/A')}")
        print(f"   Accept-Encoding: {headers.get('Accept-Encoding', 'N/A')}")
        
        print("\n✅ Requests library test PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Requests library test FAILED: {e}")
        return False


def check_with_selenium():
    """Check proxy using Selenium with selenium-wire."""
    print("\n" + "="*60)
    print("TESTING WITH SELENIUM (selenium-wire)")
    print("="*60)
    
    try:
        from seleniumwire import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure selenium-wire is installed: pip install selenium-wire")
        return False
    
    oxy_username = os.getenv('OXY_USERNAME')
    oxy_password = os.getenv('OXY_PASSWORD')
    oxy_host = os.getenv('OXY_HOST', 'pr.oxylabs.io')
    oxy_port = os.getenv('OXY_PORT', '7777')
    oxy_sticky = os.getenv('OXY_STICKY', '')
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    seleniumwire_options = {}
    
    if oxy_username and oxy_password:
        # Build username with optional sticky session
        if oxy_sticky:
            username = f"{oxy_username}-session-{oxy_sticky}"
            print(f"✅ Using sticky session: {oxy_sticky}")
        else:
            username = oxy_username
            print("ℹ️  No sticky session configured")
        
        proxy_url = f"http://{username}:{oxy_password}@{oxy_host}:{oxy_port}"
        seleniumwire_options = {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
        print(f"📍 Proxy: {oxy_host}:{oxy_port}")
        print(f"👤 Username: {username}")
    else:
        print("⚠️  No proxy credentials found. Testing with direct connection...")
    
    driver = None
    try:
        print("\nInitializing Chrome driver...")
        driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )
        print("✅ Chrome driver initialized")
        
        # Test 1: Get IP address
        print("\n[Test 1] Checking IP address...")
        driver.get('https://httpbin.org/ip')
        page_text = driver.find_element('tag name', 'body').text
        print(f"✅ Response: {page_text}")
        
        # Test 2: Check headers
        print("\n[Test 2] Checking headers...")
        driver.get('https://httpbin.org/headers')
        page_text = driver.find_element('tag name', 'body').text
        print(f"✅ Response preview:\n{page_text[:500]}...")
        
        print("\n✅ Selenium test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Selenium test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Browser closed")


def main():
    """Run both proxy checks."""
    print("\n" + "="*60)
    print("PROXY VERIFICATION TOOL")
    print("="*60)
    
    # Check environment variables
    oxy_username = os.getenv('OXY_USERNAME')
    oxy_password = os.getenv('OXY_PASSWORD')
    
    if oxy_username and oxy_password:
        print("✅ Proxy credentials found in environment")
    else:
        print("⚠️  No proxy credentials configured")
        print("   Set OXY_USERNAME and OXY_PASSWORD to test proxy")
        print("   Running tests with direct connection...\n")
    
    # Run tests
    requests_ok = check_with_requests()
    selenium_ok = check_with_selenium()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Requests test: {'✅ PASSED' if requests_ok else '❌ FAILED'}")
    print(f"Selenium test: {'✅ PASSED' if selenium_ok else '❌ FAILED'}")
    
    if requests_ok and selenium_ok:
        print("\n🎉 All tests PASSED! Proxy is configured correctly.")
        return 0
    else:
        print("\n⚠️  Some tests FAILED. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
