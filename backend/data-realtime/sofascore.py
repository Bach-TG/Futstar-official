import asyncio

import aiohttp


async def fetch_match_stats(match_id: int):
    url = f"https://api.sofascore.com/api/v1/players/794839/statistics/season/41886/tournament/17"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.sofascore.com",
        "Referer": f"https://www.sofascore.com/event/{match_id}",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"[Error] HTTP {resp.status} for {url}")
                text = await resp.text()
                print(f"Body: {text[:200]}...")
                return None

            data = await resp.json()
            return data


async def main():
    match_id = 14733285  # thay ID
    stats = await fetch_match_stats(match_id)
    print(stats)


asyncio.run(main())
