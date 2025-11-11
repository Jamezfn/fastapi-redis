import asyncio

async def fetch_data(id, sleep_time):
    print(f"Coroutine {id} starting to fetch")
    await asyncio.sleep(sleep_time)
    return {"id": id, "data": f"Sample {id}"}

async def main():
    task1 = asyncio.create_task(fetch_data(1, 2))
    task2 = asyncio.create_task(fetch_data(2, 3))
    task3 = asyncio.create_task(fetch_data(3, 4))

    res1 = await task1
    res2 = await task2
    res3 = await task3

    print(res1, res2, res3)

asyncio.run(main())
