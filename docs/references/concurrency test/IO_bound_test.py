import time
import asyncio
from IO_bound_operation import generate_files_sync, main, generate_files_multiprocessing, generate_files_async_multiprocessing

start_time = time.time()
generate_files_sync(5000, 100, 100, 'IO_Bound_test_files_sync')
end_time = time.time()
print(f'Sync time: {end_time - start_time:.2f} seconds')

start_time = time.time()
asyncio.run(main(num_files = 5000, num_lines = 100, num_numbers = 100, directory= 'IO_Bound_test_files_async'))
end_time = time.time()
print(f'AsyncIO time: {end_time - start_time:.2f} seconds')

start_time = time.time()
generate_files_multiprocessing(5000, 100, 100, 'IO_Bound_test_files_multiprocessing')
end_time = time.time()
print(f'Multiprocessing time: {end_time - start_time:.2f} seconds')

start_time = time.time()
generate_files_async_multiprocessing(5000, 100, 100, 'IO_Bound_test_files_async_multiprocessing')
end_time = time.time()
print(f'AsyncIO with multiprocessing time: {end_time - start_time:.2f} seconds')