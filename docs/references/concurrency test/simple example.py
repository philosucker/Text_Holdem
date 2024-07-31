import asyncio
import time

print(f'==== Using AsyncIO ====')

async def async_printer(name: str, times: int) -> None:
    for i in range(1, times + 1):
        print(name, i)
        await asyncio.sleep(1)

async def async_main():
    await asyncio.gather(async_printer("A", 3), async_printer("B", 3))

start_time = time.time()
asyncio.run(async_main())
end_time = time.time()
print(f'AsyncIO time: {end_time - start_time:.2f} seconds\n')

print(f'==== Not Using AsyncIO ====')

def sync_printer(name: str, times: int) -> None:
    for i in range(1, times + 1):
        print(name, i)
        time.sleep(1)

def sync_main():
    sync_printer("A", 3)
    sync_printer("B", 3)

start_time = time.time()
sync_main()
end_time = time.time()
print(f'Sync time: {end_time - start_time:.2f} seconds')
