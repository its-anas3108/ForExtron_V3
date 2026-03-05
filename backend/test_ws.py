import asyncio
import websockets

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/live/EUR_USD"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await asyncio.sleep(2)
            print("Still connected")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
