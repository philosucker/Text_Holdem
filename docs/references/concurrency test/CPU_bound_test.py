import asyncio
import time 
from CPU_bound_operation import get_target_directory, sync_main, async_main, multiprocessing_main, async_multiprocessing_main

start_time = time.time()
sync_main(get_target_directory('CPU_Bound_test_files'))
end_time = time.time()
print(f'Sync time: {end_time - start_time:.2f} seconds\n')

start_time = time.time()
asyncio.run(async_main(get_target_directory('CPU_Bound_test_files')))
end_time = time.time()
print(f'AsyncIO time: {end_time - start_time:.2f} seconds\n')

start_time = time.time()
multiprocessing_main(get_target_directory('CPU_Bound_test_files'))
end_time = time.time()
print(f'Multiprocessing time: {end_time - start_time:.2f} seconds\n')

start_time = time.time()
asyncio.run(async_multiprocessing_main(get_target_directory('CPU_Bound_test_files')))
end_time = time.time()
print(f'AsyncIO with multiprocessing time: {end_time - start_time:.2f} seconds\n')

