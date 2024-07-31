import os
import random
import aiofiles
import asyncio
import time

async def generate_files(num_files: int, num_lines: int, num_numbers: int, directory: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_directory = os.path.join(script_dir, directory)
    
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    
    for i in range(num_files):
        filename = os.path.join(target_directory, f'file_{i}.txt')
        async with aiofiles.open(filename, 'w') as f:
            for _ in range(num_lines):
                line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
                await f.write(line + '\n')

async def main():
    await generate_files(5000, 100, 100, 'test_files_2')

start_time = time.time()
# 비동기적으로 파일 생성
asyncio.run(main())
end_time = time.time()
print(f'AsyncIO time : {end_time - start_time:.2f} seconds\n')

