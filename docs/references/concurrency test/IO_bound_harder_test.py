import time
import asyncio
from IO_bound_operation import generate_files_sync, main, generate_files_multiprocessing, generate_files_async_multiprocessing

start_time = time.time()
generate_files_sync(10000, 2000, 10, 'IO_Bound_harder_test_files_sync')
end_time = time.time()
print(f'Sync time: {end_time - start_time:.2f} seconds')

start_time = time.time()
asyncio.run(main(num_files = 5000, num_lines = 1000, num_numbers = 10, directory= 'IO_Bound_harder_test_files_sync'))
end_time = time.time()
print(f'AsyncIO time: {end_time - start_time:.2f} seconds')

start_time = time.time()
generate_files_multiprocessing(10000, 2000, 10, 'IO_Bound_harder_test_files_multiprocessing')
end_time = time.time()
print(f'Multiprocessing time: {end_time - start_time:.2f} seconds')

start_time = time.time()
generate_files_async_multiprocessing(10000, 2000, 10, 'IO_Bound_harder_test_files_async_multiprocessing')
end_time = time.time()
print(f'AsyncIO with multiprocessing time: {end_time - start_time:.2f} seconds')