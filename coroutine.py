import asyncio

async def fetch_data(delay):
    print("Fetching data...")
    await asyncio.sleep(delay)
    print("Data fetched")
    return {"data": "Some data"}

async def main():
    print('Starting')
    task = await fetch_data(2)
    print('1')
    task = await fetch_data(4)

asyncio.run(main())
