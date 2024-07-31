import asyncio
import os
import aiofiles # pip install aiofiles
from concurrent.futures import ProcessPoolExecutor, as_completed

def get_target_directory(directory: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, directory)

# 동기 버전
def sync_process_file(filepath: str) -> int:
    total_product = 1
    with open(filepath, 'r') as f:
        for line in f:
            numbers = map(int, line.split())
            total_sum = sum(numbers)
            total_product *= total_sum
    return total_product

def sync_main(directory: str):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            results.append(sync_process_file(filepath))
    print(f'Sync result: {sum(results)}')


# 비동기 버전
async def async_process_file(filepath: str) -> int:
    total_product = 1
    async with aiofiles.open(filepath, 'r') as f:
        async for line in f:
            numbers = map(int, line.split())
            total_sum = sum(numbers)
            total_product *= total_sum
    return total_product

async def async_main(directory: str):
    tasks = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            tasks.append(async_process_file(filepath))
    results = await asyncio.gather(*tasks)
    print(f'AsyncIO result: {sum(results)}')


# 멀티프로세싱 버전
def multiprocessing_main(directory: str):
    results = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(sync_process_file, os.path.join(directory, filename))
                   for filename in os.listdir(directory) if filename.endswith('.txt')]
        for future in as_completed(futures):
            results.append(future.result())
    print(f'Multiprocessing result: {sum(results)}')


# 비동기 + 멀티프로세싱 버전
async def process_file_in_executor(executor, filepath: str) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, sync_process_file, filepath)

async def async_multiprocessing_main(directory: str):
    tasks = []
    with ProcessPoolExecutor() as executor:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                filepath = os.path.join(directory, filename)
                tasks.append(process_file_in_executor(executor, filepath))
        results = await asyncio.gather(*tasks)
        print(f'AsyncIO with multiprocessing result: {sum(results)}')

