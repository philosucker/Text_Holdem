import asyncio

async def f():
    await asyncio.sleep(0)
    return 123

loop = asyncio.get_event_loop()  
coro = f()
result = loop.run_until_complete(coro)
print(result)