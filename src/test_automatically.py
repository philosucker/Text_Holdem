import sys
import io
import os

# test_manually.py 파일의 절대 경로를 명확히 지정합니다.
script_path = "/home/philosucker/holdem/공부중/src/test_manually.py"
test_cases_dir = "/home/philosucker/holdem/공부중/src/test_cases_dealer"  # 테스트 케이스 파일이 있는 디렉토리 경로

# 디렉토리 내의 모든 텍스트 파일을 가져옵니다.
test_files = [f for f in os.listdir(test_cases_dir) if f.endswith('.txt')]

# 기존 stdin을 백업합니다.
original_stdin = sys.stdin

for test_file in test_files:
    # 각 테스트 파일을 읽습니다.
    with open(os.path.join(test_cases_dir, test_file), 'r') as f:
        input_text = f.read()
    
    # StringIO 객체를 생성하여 입력 텍스트로 사용합니다.
    sys.stdin = io.StringIO(input_text)
    
    # test_manually.py 스크립트를 실행합니다.
    with open(script_path) as f:
        exec(f.read())

    print(f"Test case {test_file} executed.")

# 모든 테스트가 끝난 후 stdin을 원래대로 복원합니다.
sys.stdin = original_stdin
