"""
Human-like behavior utilities for web scraping.
Adds realistic delays, mouse movements, and interactions to avoid bot detection.
"""

import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

def inject_stealth_javascript(driver):
    """Inject JavaScript to mask automation signals and make the browser appear more human."""
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            '''
        })
        print("✅ Stealth JavaScript injected")
        return True
    except Exception as e:
        print(f"⚠️  Could not inject stealth JavaScript: {e}")
        return False

def random_delay(min_seconds=2, max_seconds=5):
    """Add a random delay to simulate human reading/thinking time."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def human_type(element, text, typing_speed=0.1):
    """Type text with random delays between keystrokes like a human."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, typing_speed))

def random_mouse_movement(driver):
    """Simulate random mouse movements across the page."""
    try:
        actions = ActionChains(driver)
        # Get page dimensions
        width = driver.execute_script("return document.body.scrollWidth")
        height = driver.execute_script("return document.body.scrollHeight")
        
        # Perform 2-4 random movements
        for _ in range(random.randint(2, 4)):
            x = random.randint(0, min(width, 1920))
            y = random.randint(0, min(height, 1080))
            # Use move_by_offset from center to avoid out-of-bounds issues
            try:
                actions.move_by_offset(x - 960, y - 540)
                actions.perform()
                time.sleep(random.uniform(0.1, 0.3))
                actions = ActionChains(driver)  # Reset actions
            except WebDriverException:
                continue  # Skip this movement if it fails
    except WebDriverException:
        pass  # Silently fail if movement doesn't work

def smooth_scroll(driver, scroll_pause_time=0.5):
    """Scroll down the page gradually like a human reading."""
    try:
        # Get total page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll in chunks
        current_position = 0
        scroll_increment = random.randint(200, 400)
        
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            current_position += scroll_increment
            time.sleep(random.uniform(0.3, scroll_pause_time))
            
            # Occasionally scroll back up a bit (human-like)
            if random.random() < 0.2:
                scroll_back = random.randint(50, 150)
                current_position -= scroll_back
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.2, 0.4))
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.3, 0.6))
    except WebDriverException:
        pass

def hover_random_elements(driver, num_hovers=2):
    """Hover over random elements on the page."""
    try:
        # Find interactive elements
        elements = driver.find_elements(By.CSS_SELECTOR, "a, button, input")
        if not elements:
            return
        
        actions = ActionChains(driver)
        for _ in range(min(num_hovers, len(elements))):
            element = random.choice(elements)
            try:
                actions.move_to_element(element).perform()
                time.sleep(random.uniform(0.2, 0.5))
            except WebDriverException:
                continue
    except WebDriverException:
        pass

def simulate_reading(driver, min_seconds=3, max_seconds=7):
    """Simulate a user reading the page content."""
    print(f"📖 Simulating reading time...")
    
    # Random scroll while "reading"
    scroll_times = random.randint(2, 4)
    read_time = random.uniform(min_seconds, max_seconds)
    scroll_interval = read_time / scroll_times
    
    for _ in range(scroll_times):
        scroll_amount = random.randint(100, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_interval)
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(0.5, 1.0))

def wait_for_page_load(driver, timeout=10):
    """Wait for page to fully load including images and scripts."""
    try:
        # Wait for document ready state
        for _ in range(timeout):
            ready_state = driver.execute_script("return document.readyState")
            if ready_state == "complete":
                break
            time.sleep(0.5)
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(1, 2))
    except WebDriverException:
        pass

def natural_click(driver, element):
    """Click an element with human-like behavior."""
    try:
        # Move mouse to element first
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(random.uniform(0.2, 0.5))
        
        # Click
        element.click()
        
        # Wait after click
        time.sleep(random.uniform(0.5, 1.5))
    except WebDriverException:
        # Fallback to regular click
        element.click()
        time.sleep(random.uniform(0.5, 1.5))

def add_human_behavior_to_login(driver, email_element, password_element, submit_element, email, password):
    """Add human-like behavior to the login process."""
    print("🤖 Adding human-like login behavior...")
    
    # Move mouse randomly before starting
    random_mouse_movement(driver)
    random_delay(1, 2)
    
    # Focus on email field naturally
    natural_click(driver, email_element)
    random_delay(0.5, 1)
    
    # Type email with human speed
    human_type(email_element, email, typing_speed=0.15)
    random_delay(0.5, 1.5)
    
    # Tab or click to password field
    natural_click(driver, password_element)
    random_delay(0.5, 1)
    
    # Type password with human speed
    human_type(password_element, password, typing_speed=0.12)
    random_delay(1, 2)
    
    # Hover over submit button before clicking
    actions = ActionChains(driver)
    actions.move_to_element(submit_element).perform()
    random_delay(0.5, 1)
    
    # Click submit
    natural_click(driver, submit_element)

def add_human_behavior_to_navigation(driver):
    """Add human-like behavior when navigating to a new page."""
    print("🤖 Adding human-like navigation behavior...")
    
    # Wait for page to load
    wait_for_page_load(driver)
    
    # Move mouse around
    random_mouse_movement(driver)
    
    # Scroll and read
    simulate_reading(driver, min_seconds=2, max_seconds=4)
    
    # Hover over some elements
    hover_random_elements(driver, num_hovers=2)
    
    # Final delay before taking action
    random_delay(1, 2)
