import asyncio
from magi_core.providers.sniff import SniffProvider


async def main():
    print("Testing SniffProvider...")
    try:
        # Assuming localhost:8080 is running OpenWebUI
        provider = SniffProvider(url="http://localhost:8080", headless=True)

        print("Checking health...")
        if await provider.health_check():
            print("Health Check: OK")

            print("Generating response...")
            response = await provider.generate("Are you there?")
            print(f"Response: {response.content}")
        else:
            print("Health Check: FAILED (Is OpenWebUI running at localhost:8080?)")

    except Exception as e:
        print(f"Error: {e}")
        try:
            provider.debug_screenshot()
        except Exception:  # Fixed bare except
            pass


if __name__ == "__main__":
    asyncio.run(main())
