
import os

def ensure_directory(directory: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_directory = os.path.join(script_dir, directory)
    os.makedirs(target_directory, exist_ok=True)
    return target_directory

import random
import time

def generate_files_sync(num_files: int, num_lines: int, num_numbers: int, directory: str):
    target_directory = ensure_directory(directory)
    
    for i in range(num_files):
        filename = os.path.join(target_directory, f'file_{i}.txt')
        with open(filename, 'w') as f:
            for _ in range(num_lines):
                line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
                f.write(line + '\n')

import aiofiles
import asyncio

async def generate_files_async(num_files: int, num_lines: int, num_numbers: int, directory: str):
    target_directory = ensure_directory(directory)
    
    for i in range(num_files):
        filename = os.path.join(target_directory, f'file_{i}.txt')
        async with aiofiles.open(filename, 'w') as f:
            for _ in range(num_lines):
                line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
                await f.write(line + '\n')

async def main(num_files: int, num_lines: int, num_numbers: int, directory: str):
    await generate_files_async(num_files , num_lines, num_numbers, directory)

import multiprocessing

def write_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    target_directory = ensure_directory(directory)
    filename = os.path.join(target_directory, f'file_{file_index}.txt')
    with open(filename, 'w') as f:
        for _ in range(num_lines):
            line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
            f.write(line + '\n')

def generate_files_multiprocessing(num_files: int, num_lines: int, num_numbers: int, directory: str):
    with multiprocessing.Pool() as pool:
        pool.starmap(write_file, [(i, num_lines, num_numbers, directory) for i in range(num_files)])

from concurrent.futures import ProcessPoolExecutor

async def async_write_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    target_directory = ensure_directory(directory)
    filename = os.path.join(target_directory, f'file_{file_index}.txt')
    async with aiofiles.open(filename, 'w') as f:
        for _ in range(num_lines):
            line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
            await f.write(line + '\n')

def sync_write_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    asyncio.run(async_write_file(file_index, num_lines, num_numbers, directory))

def generate_files_async_multiprocessing(num_files: int, num_lines: int, num_numbers: int, directory: str):
    with ProcessPoolExecutor() as executor:
        executor.map(sync_write_file, range(num_files), [num_lines]*num_files, [num_numbers]*num_files, [directory]*num_files)
