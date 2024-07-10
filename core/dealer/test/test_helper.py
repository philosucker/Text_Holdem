import configparser
import sys
import os

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

def just_get_input(self):
    if self.config.getboolean('DEFAULT', 'just_get_input'):
        input_line = sys.stdin.readline().strip()
        parts = input_line.split()
        
        if len(parts) == 2:
            key = parts[0]
            try:
                value = int(parts[1])
            except ValueError:
                value = None
        elif len(parts) == 1:
            key = parts[0]
            value = None
        else:
            raise ValueError("Invalid input format. Expected format: 'string' or 'string int'")
        return {key: value}

def get_input_prompt(self, prompt):
    if self.config.getboolean('DEFAULT', 'get_input_prompt'):
        print(prompt)
        input_line = sys.stdin.readline().strip()
        parts = input_line.split()
        
        if len(parts) == 2:
            key = parts[0]
            try:
                value = int(parts[1])
            except ValueError:
                value = None
        elif len(parts) == 1:
            key = parts[0]
            value = None
        else:
            raise ValueError("Invalid input format. Expected format: 'string' or 'string int'")
        return {key: value}

def test_code_action_info(self, current_player, possible_actions, street_name):
    if self.config.getboolean('DEFAULT', 'test_code_action_info'):
        print(f'{street_name} 스트리트 입니다')
        stack_size = self.players[current_player]['stk_size']
        print(f'LPFB : {self.LPFB}')
        print(f'prev_VALID : {self.prev_VALID}')
        print(f'prev_TOTAL : {self.prev_TOTAL}')
        print(f'{current_player} 님의 현재 스택사이즈는 {stack_size}입니다')
        print(f'{current_player} 님의 가능한 액션은 {possible_actions} 입니다') 
        answer = self.get_input_prompt(f'{current_player} 님 액션을 입력해 주세요')    
        print(f'{current_player}님의 액션은 {next(iter(answer))} 입니다')
        print()
        return answer

def test_code_street_info(self, street_name):
    if self.config.getboolean('DEFAULT', 'test_code_street_info'):
        print()
        print(f'==============={street_name} 스트리트===============')
        print(f'actioned_queue: {self.actioned_queue}')
        print(f'fold_users: {self.fold_users}')
        print(f'fold_users_total: {self.fold_users_total}')
        print(f'all_in_users: {self.all_in_users}')
        print(f'all_in_users_total: {self.all_in_users_total}')
        print()
        print(f'일어난 모든 액션들의 내용을 일어난 순서대로 기록: {self.log_hand_actions}')
        print(f'pot_total : {self.pot_total}')
        print(f'생존자 : {self.survivors}')
        print()

def test_code_showdown_info(self):
    if self.config.getboolean('DEFAULT', 'test_code_showdown_info'):
        print("=====================쇼다운 결과=====================")
        print(f'best hands : {self.log_best_hands}')
        print(f'nuts : {self.log_nuts}')
        print()

def test_code_pot_award_info(self, stk_size):
    if self.config.getboolean('DEFAULT', 'test_code_pot_award_info'):
        log_nuts_length = int(self.config['DEFAULT']['log_nuts_length'])
        if len(self.log_nuts) == log_nuts_length:
            print("=====================팟분배 결과=====================")
            print(f'users_ranking : {self.log_users_ranking}')
            for id, position in zip(stk_size, self.players):
                stack_size = self.players[position]['stk_size']
                print(f'{position} 의 stk_size 변화 : {stk_size[id]} -> {stack_size}')
