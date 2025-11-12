import asyncio

async def fetch_data(id, sleep_time):
    print(f"Coroutine {id} starting to fetch")
    await asyncio.sleep(sleep_time)
    return {"id": id, "data": f"Sample {id}"}

async def main():
    result = await asyncio.gather(fetch_data(1, 2), fetch_data(1, 2), fetch_data(1, 2))
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for i, j in enumerate([1, 2, 3], start=1):
            task = tg.create_task(fetch_data(i, j))
            tasks.append(task)
    
    result = [task.result() for task in tasks]

    for res in result:
        print(f'Received result: {res}')

asyncio.run(main())
