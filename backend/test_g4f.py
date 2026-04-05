import asyncio
import g4f
from g4f.client import AsyncClient
async def main():
    client = AsyncClient(provider=g4f.Provider.DuckDuckGo)
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
