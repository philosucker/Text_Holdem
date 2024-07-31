import os
import random
import asyncio
import aiofiles
import time
from concurrent.futures import ProcessPoolExecutor

async def async_write_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_directory = os.path.join(script_dir, directory)
    
    if not os.path.exists(target_directory):
        os.makedirs(target_directory, exist_ok=True)
    
    filename = os.path.join(target_directory, f'file_{file_index}.txt')
    async with aiofiles.open(filename, 'w') as f:
        for _ in range(num_lines):
            line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
            await f.write(line + '\n')

def sync_write_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    # asyncio.run을 사용하여 각 파일을 비동기적으로 생성
    asyncio.run(async_write_file(file_index, num_lines, num_numbers, directory))

def generate_files(num_files: int, num_lines: int, num_numbers: int, directory: str):
    with ProcessPoolExecutor() as executor:
        # ProcessPoolExecutor를 사용하여 파일 생성 작업을 병렬로 수행
        executor.map(sync_write_file, range(num_files), [num_lines]*num_files, [num_numbers]*num_files, [directory]*num_files)


start_time = time.time()
# 멀티프로세싱과 비동기 I/O를 결합하여 파일 생성
generate_files(5000, 100, 100, 'test_files_4')
end_time = time.time()
print(f'AsyncIO with multiprocessing time: {end_time - start_time:.2f} seconds\n')
