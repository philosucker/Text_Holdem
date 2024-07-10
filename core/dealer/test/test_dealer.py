import sys
import io
import os
import configparser
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from dealer import Dealer

config_file_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)

# config.ini 파일의 경로를 절대 경로로 지정합니다.
config_file_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)

test_cases_dir = "/home/philosucker/holdem/core/dealer/test/test_cases"

# 수동 테스트
def run_manual_test():
    rings = 6  # robby 에서 전달 받음
    user_id_list = ['1', '2', '3', '4', '5', '6']  # robby 에서 전달 받음
    stakes = "low"  # robby 에서 전달 받음

    try:
        # 설정 파일에서 stk_size 값을 가져옴
        print(f"Config file path: {config_file_path}")  # 설정 파일 경로 출력
        print(f"Config sections: {config.sections()}")  # 설정 파일 섹션 출력
        print(f"Config items in DEFAULT: {config.items('DEFAULT')}")  # 설정 파일의 항목 출력
        
        stk_size_values = list(map(int, config['DEFAULT']['stk_size'].split(',')))
        stk_size = {str(i + 1): stk_size_values[i] for i in range(len(stk_size_values))}
    except KeyError as e:
        print(f"Error: {e} not found in config file.")
        sys.exit(1)
    except ValueError:
        print("Error: 'stk_size' values in config file are not valid integers.")
        sys.exit(1)

    dealer = Dealer(user_id_list, stk_size, rings, stakes)
    dealer.go_street(stk_size)

# 자동 테스트
def run_auto_test():
    test_files = [f for f in os.listdir(test_cases_dir) if f.endswith('.txt')]
    original_stdin = sys.stdin

    for test_file in test_files:
        with open(os.path.join(test_cases_dir, test_file), 'r') as f:
            input_text = f.read()
        
        print(f"Test case '{test_file}' starts.")
        sys.stdin = io.StringIO(input_text)
        run_manual_test()
        print(f"Test case '{test_file}' ends.")

    sys.stdin = original_stdin

# 다중 테스트
def run_multiple_tests():
    test_files = [f for f in os.listdir(test_cases_dir) if f.endswith('.txt')]
    original_stdin = sys.stdin

    for test_file in test_files:
        with open(os.path.join(test_cases_dir, test_file), 'r') as f:
            input_text = f.read()

        try:
            for i in range(100000):
                sys.stdin = io.StringIO(input_text)
                run_manual_test()
        except AssertionError:
            print(f"AssertionError occurred during test case '{test_file}' iteration {i+1}.")
            traceback.print_exc()
        except SystemExit as e:
            print(f"SystemExit occurred during test case '{test_file}' iteration {i+1}.")
            print(f"Error: {e}")
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"Error occurred during test case '{test_file}' iteration {i+1}.")
            print(f"Error: {e}")
            traceback.print_exc()

    sys.stdin = original_stdin

def run_tests():
    print("Choose test mode: [manual|auto|multiple]")
    mode = input().strip().lower()

    if mode == 'manual':
        run_manual_test()
    elif mode == 'auto':
        run_auto_test()
    elif mode == 'multiple':
        run_multiple_tests()
    else:
        print("Invalid mode. Choose from 'manual', 'auto', or 'multiple'.")

if __name__ == "__main__":
    run_tests()
