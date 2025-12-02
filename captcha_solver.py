"""
CAPTCHA Solver Module for KenPom Scraping Scripts

This module provides automatic CAPTCHA detection and solving capabilities
using the 2captcha service. It supports multiple CAPTCHA types:
- reCAPTCHA v2
- hCaptcha
- Cloudflare Turnstile

Usage:
    from captcha_solver import CaptchaSolver
    
    solver = CaptchaSolver(api_key="your_2captcha_api_key")
    solver.detect_and_solve(driver, current_url)
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CaptchaSolver:
    """
    A class to detect and solve various types of CAPTCHAs on web pages.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the CAPTCHA solver.
        
        Args:
            api_key (str, optional): 2captcha API key. If None, solver will
                                     detect CAPTCHAs but not solve them.
        """
        self.api_key = api_key
        self.solver = None
        
        if api_key:
            try:
                from twocaptcha import TwoCaptcha
                self.solver = TwoCaptcha(api_key)
                print("✅ 2captcha solver initialized successfully")
            except ImportError:
                print("⚠️  Warning: 2captcha-python not installed. CAPTCHA solving disabled.")
                print("   Install with: pip install 2captcha-python")
            except Exception as e:
                print(f"⚠️  Warning: Failed to initialize 2captcha solver: {e}")
        else:
            print("ℹ️  No 2captcha API key provided. CAPTCHA detection only (no solving).")
    
    def detect_captcha_type(self, driver):
        """
        Detect which type of CAPTCHA is present on the current page.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            tuple: (captcha_type, sitekey) or (None, None) if no CAPTCHA found
                   captcha_type can be: 'recaptcha_v2', 'hcaptcha', 'turnstile'
        """
        try:
            # Check for reCAPTCHA v2
            recaptcha_elements = driver.find_elements(By.CLASS_NAME, "g-recaptcha")
            if recaptcha_elements:
                sitekey = recaptcha_elements[0].get_attribute("data-sitekey")
                if sitekey:
                    print(f"🔍 Detected reCAPTCHA v2 (sitekey: {sitekey[:20]}...)")
                    return ("recaptcha_v2", sitekey)
            
            # Check for reCAPTCHA v2 iframe
            try:
                driver.switch_to.default_content()
                recaptcha_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                if recaptcha_iframes:
                    # Try to extract sitekey from iframe src
                    iframe_src = recaptcha_iframes[0].get_attribute("src")
                    if "k=" in iframe_src:
                        sitekey = iframe_src.split("k=")[1].split("&")[0]
                        print(f"🔍 Detected reCAPTCHA v2 iframe (sitekey: {sitekey[:20]}...)")
                        return ("recaptcha_v2", sitekey)
            except Exception:
                pass
            
            # Check for hCaptcha
            hcaptcha_elements = driver.find_elements(By.CLASS_NAME, "h-captcha")
            if hcaptcha_elements:
                sitekey = hcaptcha_elements[0].get_attribute("data-sitekey")
                if sitekey:
                    print(f"🔍 Detected hCaptcha (sitekey: {sitekey[:20]}...)")
                    return ("hcaptcha", sitekey)
            
            # Check for hCaptcha iframe
            try:
                driver.switch_to.default_content()
                hcaptcha_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha')]")
                if hcaptcha_iframes:
                    iframe_src = hcaptcha_iframes[0].get_attribute("src")
                    if "sitekey=" in iframe_src:
                        sitekey = iframe_src.split("sitekey=")[1].split("&")[0]
                        print(f"🔍 Detected hCaptcha iframe (sitekey: {sitekey[:20]}...)")
                        return ("hcaptcha", sitekey)
            except Exception:
                pass
            
            # Check for Cloudflare Turnstile
            turnstile_elements = driver.find_elements(By.CLASS_NAME, "cf-turnstile")
            if turnstile_elements:
                sitekey = turnstile_elements[0].get_attribute("data-sitekey")
                if sitekey:
                    print(f"🔍 Detected Cloudflare Turnstile (sitekey: {sitekey[:20]}...)")
                    return ("turnstile", sitekey)
            
            # Check for Turnstile in page source as fallback
            page_source = driver.page_source.lower()
            if "turnstile" in page_source or "cf-turnstile" in page_source:
                print("🔍 Detected possible Cloudflare Turnstile (sitekey not found)")
                return ("turnstile", None)
            
        except Exception as e:
            print(f"⚠️  Error during CAPTCHA detection: {e}")
        
        return (None, None)
    
    def solve_recaptcha_v2(self, driver, sitekey, url):
        """
        Solve a reCAPTCHA v2 challenge.
        
        Args:
            driver: Selenium WebDriver instance
            sitekey: The site key for the reCAPTCHA
            url: The URL of the page
            
        Returns:
            bool: True if solved successfully, False otherwise
        """
        if not self.solver:
            print("❌ Cannot solve CAPTCHA: No API key provided or solver not initialized")
            return False
        
        try:
            print("🔓 Solving reCAPTCHA v2...")
            result = self.solver.recaptcha(sitekey=sitekey, url=url)
            token = result['code']
            
            # Inject the token into the page
            script = f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
            driver.execute_script(script)
            
            # Also try to set it in the textarea (some sites use this)
            script = f'document.querySelector("[name=g-recaptcha-response]").value="{token}";'
            driver.execute_script(script)
            
            print("✅ reCAPTCHA v2 solved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to solve reCAPTCHA v2: {e}")
            return False
    
    def solve_hcaptcha(self, driver, sitekey, url):
        """
        Solve an hCaptcha challenge.
        
        Args:
            driver: Selenium WebDriver instance
            sitekey: The site key for the hCaptcha
            url: The URL of the page
            
        Returns:
            bool: True if solved successfully, False otherwise
        """
        if not self.solver:
            print("❌ Cannot solve CAPTCHA: No API key provided or solver not initialized")
            return False
        
        try:
            print("🔓 Solving hCaptcha...")
            result = self.solver.hcaptcha(sitekey=sitekey, url=url)
            token = result['code']
            
            # Inject the token into the page
            script = f'document.querySelector("[name=h-captcha-response]").value="{token}";'
            driver.execute_script(script)
            
            print("✅ hCaptcha solved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to solve hCaptcha: {e}")
            return False
    
    def solve_turnstile(self, driver, sitekey, url):
        """
        Solve a Cloudflare Turnstile challenge.
        
        Args:
            driver: Selenium WebDriver instance
            sitekey: The site key for the Turnstile
            url: The URL of the page
            
        Returns:
            bool: True if solved successfully, False otherwise
        """
        if not self.solver:
            print("❌ Cannot solve CAPTCHA: No API key provided or solver not initialized")
            return False
        
        try:
            print("🔓 Solving Cloudflare Turnstile...")
            result = self.solver.turnstile(sitekey=sitekey, url=url)
            token = result['code']
            
            # Inject the token into the page
            script = f'document.querySelector("[name=cf-turnstile-response]").value="{token}";'
            driver.execute_script(script)
            
            print("✅ Cloudflare Turnstile solved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to solve Cloudflare Turnstile: {e}")
            return False
    
    def detect_and_solve(self, driver, url):
        """
        Detect and solve any CAPTCHA present on the current page.
        
        This is the main method to use in scraping scripts. It will:
        1. Detect if a CAPTCHA is present
        2. Identify the type of CAPTCHA
        3. Solve it if an API key is available
        4. Wait briefly after solving
        
        Args:
            driver: Selenium WebDriver instance
            url: The current URL of the page
            
        Returns:
            bool: True if no CAPTCHA found or if CAPTCHA solved successfully,
                  False if CAPTCHA found but couldn't be solved
        """
        # Give the page a moment to fully load
        time.sleep(1)
        
        captcha_type, sitekey = self.detect_captcha_type(driver)
        
        if captcha_type is None:
            print("✅ No CAPTCHA detected on page")
            return True
        
        if not self.solver:
            print(f"⚠️  {captcha_type.upper()} detected but no API key available to solve it")
            return False
        
        # Solve based on type
        success = False
        if captcha_type == "recaptcha_v2" and sitekey:
            success = self.solve_recaptcha_v2(driver, sitekey, url)
        elif captcha_type == "hcaptcha" and sitekey:
            success = self.solve_hcaptcha(driver, sitekey, url)
        elif captcha_type == "turnstile" and sitekey:
            success = self.solve_turnstile(driver, sitekey, url)
        else:
            print(f"⚠️  Cannot solve {captcha_type}: missing sitekey")
            return False
        
        if success:
            # Wait a bit after solving to appear more human-like
            print("⏳ Waiting 2 seconds after solving CAPTCHA...")
            time.sleep(2)
        
        return success
