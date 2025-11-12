import asyncio

async def fetch_data(id, sleep_time):
    print(f"Coroutine {id} starting to fetch")
    await asyncio.sleep(sleep_time)
    return {"id": id, "data": f"Sample {id}"}

async def main():
    result = await asyncio.gather(fetch_data(1, 2), fetch_data(1, 2), fetch_data(1, 2))
    
    for res in result:
        print(res)

asyncio.run(main())
