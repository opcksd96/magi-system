import asyncio
from magi_core.providers.sniff import SniffProvider

# Instructions:
# 1. Ensure OpenWebUI is running at http://localhost:8080
# 2. Update EMAIL and PASSWORD below if changed from defaults
# 3. Run: python verify_sniff.py


async def main():
    print("Verifying SniffProvider...")
    try:
        provider = SniffProvider(
            url="http://localhost:8080",
            headless=False,  # Run visible to see what happens
            email="w77cf87b3f3yg@gmail.com",
            password="gv7SCDR@YfANdH4",
        )

        print("1. Health/Connectivity Check...")
        if await provider.health_check():
            print("   [OK] Connected to OpenWebUI")

            print("2. Generating Response...")
            # Simple prompt to test end-to-end
            response = await provider.generate("Hello, are you online?")
            print(f"   [OK] Received response: {response.content}")
            print(f"   (Token usage: {response.token_usage})")
        else:
            print("   [FAILED] Could not connect to OpenWebUI")

    except Exception as e:
        print(f"   [ERROR] {e}")
        # provider.debug_screenshot() # Uncomment to save screenshot on error


if __name__ == "__main__":
    asyncio.run(main())
