import asyncio

async def fetch_data(future, value):
    await asyncio.sleep(2)
    future.set_result(value)

async def main():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    asyncio.create_task(fetch_data(future, 'Future result is here'))

    result = await future
    print(result)

asyncio.run(main())
