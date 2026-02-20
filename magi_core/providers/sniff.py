import asyncio
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from magi_core.providers.base import ModelProvider, MagiResponse

# Robust JS Logic extracted from test.py
JS_LOGIC = """
window.magiSniffer = {
    waitForElement: async (selector, timeout = 3000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(selector);
            if (el) return el;
            await new Promise(r => setTimeout(r, 100));
        }
        return null;
    },

    selectModel: async function(targetModelValue) {
        try {
            const selectorBtn = document.querySelector('button[aria-label="Model Selector"]'); // Adjusted selector guess
            // Fallback for OpenWebUI specific selector if specific label changes
            const fallbackBtn = document.querySelector('#model-selector'); 

            const btn = selectorBtn || fallbackBtn;
            if (!btn) return false;

            if (btn.getAttribute('aria-expanded') !== 'true') {
                btn.click();
            }

            for (let i = 0; i < 30; i++) { 
                await new Promise(r => setTimeout(r, 200)); 
                const target = document.querySelector(`button[data-value="${targetModelValue}"]`);
                if (target) {
                    target.scrollIntoView({ block: 'center' });
                    await new Promise(r => setTimeout(r, 500)); 
                    target.click();
                    return true; 
                }
            }
        } catch (e) {
            console.error("[MAGI] JS Error during selectModel:", e);
        }
        return false;
    },

    injectPrompt: async function(prompt) {
        const maxRetries = 10;
        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

        for (let i = 0; i < maxRetries; i++) {
            const el = document.querySelector('#chat-textarea'); // Standard OpenWebUI ID
            if (el) {
                el.focus();
                el.value = prompt;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                
                await sleep(200);
                const btn = document.querySelector('button[type="submit"]');
                if (btn && !btn.disabled) {
                    btn.click();
                    return true;
                }
            }
            await sleep(500);
        }
        return false;
    },

    getLastResponse: function() {
        // Look for message content. OpenWebUI structure changes often, but let's try standard classes.
        const messages = document.querySelectorAll('.message-content'); 
        # Alternatively check for .chat-assistant if specific class is used
        
        if (messages.length === 0) return "";
        
        // Get the last one
        return messages[messages.length - 1].innerText.trim();
    },

    getTokenUsage: async function() {
        // Try to find token info. This is tricky and implementation specific.
        // Returning null for now to be safe, can be enhanced.
        return null;
    }
};
"""

# Re-injecting the exact extracted JS from test.py because my manual adjustment above might be wrong
# regarding specific selectors (e.g. #chat-input vs #chat-textarea).
# test.py used #chat-input and .chat-assistant. I will respect that.

JS_LOGIC_ROBUST = """
window.magiSniffer = {
    waitForElement: async (selector, timeout = 3000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(selector);
            if (el) return el;
            await new Promise(r => setTimeout(r, 100));
        }
        return null;
    },

    selectModel: async function(targetModelValue) {
        try {
            const selectorBtn = document.querySelector('button[aria-label="Select model"]');
            if (!selectorBtn) selectorBtn = document.querySelector('#model-selector');
            
            if (!selectorBtn) return false;

            if (selectorBtn.getAttribute('aria-expanded') !== 'true') {
                selectorBtn.click();
            }

            for (let i = 0; i < 30; i++) { 
                await new Promise(r => setTimeout(r, 200)); 
                const target = document.querySelector(`button[data-value^="${targetModelValue}"]`);
                if (target) {
                    target.scrollIntoView({ block: 'center' });
                    await new Promise(r => setTimeout(r, 500)); 
                    target.click();
                    return true; 
                }
            }
        } catch (e) {
            console.error(e);
        }
        return false;
    },

    injectPrompt: async function(prompt) {
        const selectors = ['#chat-input', '#chat-textarea', 'textarea[id^="chat"]', 'textarea.w-full', 'textarea'];
        let el = null;
        for (const sel of selectors) {
             const found = document.querySelector(sel);
             if (found && found.offsetParent !== null) { 
                 el = found;
                 break;
             }
        }
        
        if (!el) {
             el = await this.waitForElement('#chat-input', 2000) || await this.waitForElement('#chat-textarea', 2000);
        }

        if (el) {
            el.focus(); 
            el.value = prompt;
            el.dispatchEvent(new Event('input', { bubbles: true }));
             await new Promise(r => setTimeout(r, 500));
            
            const btn = document.querySelector('button[type="submit"]') || document.querySelector('button[aria-label="Send message"]');
            
            if (btn && !btn.disabled) { 
                btn.click(); 
                return true; 
            }
        }
        return false;
    },

    getLastResponse: function() {
         const msgs = document.querySelectorAll('.chat-assistant .message-content');
         if (msgs.length === 0) return "";
         return msgs[msgs.length - 1].innerText.trim();
    }
};
"""


class SniffProvider(ModelProvider):
    def __init__(
        self,
        url: str = "http://localhost:8080",
        headless: bool = True,
        email: str = "w77cf87b3f3yg@gmail.com",
        password: str = "gv7SCDR@YfANdH4",
    ):
        self.url = url
        self.headless = headless
        self.email = email
        self.password = password
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_driver()

    def _setup_driver(self):
        options = Options()
        if self.headless:
            # options.add_argument("--headless=new")
            pass
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.url)
        time.sleep(2)

        # Check for login
        try:
            email_input = self.driver.find_element(By.CSS_SELECTOR, "#email")
            if email_input:
                email_input.send_keys(self.email)
                self.driver.find_element(By.CSS_SELECTOR, "#password").send_keys(
                    self.password
                )
                self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                ).click()
                time.sleep(3)  # Wait for login
        except Exception:
            # Maybe already logged in or no login required
            pass

        self.driver.execute_script(JS_LOGIC_ROBUST)

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> MagiResponse:
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        # 1. Inject
        success = self.driver.execute_script(
            f"return window.magiSniffer.injectPrompt({repr(prompt)});"
        )
        if not success:
            # Try re-injecting JS if page reloaded
            self.driver.execute_script(JS_LOGIC_ROBUST)
            success = self.driver.execute_script(
                f"return window.magiSniffer.injectPrompt({repr(prompt)});"
            )
            if not success:
                raise RuntimeError("Failed to inject prompt")

        # 2. Wait for response
        prev_text = ""
        stable_count = 0
        final_text = ""

        for _ in range(60):  # 60 seconds max
            await asyncio.sleep(1)
            text = self.driver.execute_script(
                "return window.magiSniffer.getLastResponse();"
            )

            if text and text == prev_text and len(text) > 0:
                stable_count += 1
            else:
                stable_count = 0

            prev_text = text

            if stable_count >= 3:  # Stable for 3 seconds
                final_text = text
                break

        return MagiResponse(
            content=final_text,
            model_name="SniffedModel",
            provider_name="SniffProvider",
            token_usage={"estimated": len(final_text) // 4},
        )

    async def health_check(self) -> bool:
        if not self.driver:
            return False
        try:
            return self.driver.execute_script("return !!document.body;")
        except Exception:  # noqa: BLE001
            return False

    def debug_screenshot(self, filename: str = "debug.png"):
        if self.driver:
            self.driver.save_screenshot(filename)
            print(f"Screenshot saved to {filename}")
            print(f"Current URL: {self.driver.current_url}")
            try:
                print(
                    f"Body text snippet: {self.driver.find_element(By.TAG_NAME, 'body').text[:500]}"
                )
            except Exception:
                pass

    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
