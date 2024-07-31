import os
import random
import time
import multiprocessing

def generate_file(file_index: int, num_lines: int, num_numbers: int, directory: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_directory = os.path.join(script_dir, directory)

    if not os.path.exists(target_directory):
        os.makedirs(target_directory, exist_ok=True)
    
    filename = os.path.join(target_directory, f'file_{file_index}.txt')
    with open(filename, 'w') as f:
        for _ in range(num_lines):
            line = ' '.join(str(random.randint(1, 9)) for _ in range(num_numbers))
            f.write(line + '\n')

def generate_files(num_files: int, num_lines: int, num_numbers: int, directory: str):
    # 멀티프로세싱 풀 생성
    with multiprocessing.Pool() as pool:
        pool.starmap(generate_file, [(i, num_lines, num_numbers, directory) for i in range(num_files)])


start_time = time.time()
# 멀티프로세싱으로 파일 생성
generate_files(5000, 100, 100, 'test_files_3')
end_time = time.time()
print(f'Multiprocessing time: {end_time - start_time:.2f} seconds\n')
