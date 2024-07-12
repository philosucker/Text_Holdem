
import configparser
import sys
import os
from src import Base

current_dir = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.join(current_dir, 'test')
sys.path.append(test_dir)

from test_helper import *

class Dealer(Base):

    def __init__(self, user_id_list : list, stk_size : list, rings : int, stakes : str) -> None:
        super().__init__(user_id_list, stk_size, rings, stakes)

        self.config = configparser.ConfigParser()
        self.config.read('/home/philosucker/holdem/core/dealer/test/config.ini')
        self.just_get_input = just_get_input.__get__(self)
        self.get_input_prompt = get_input_prompt.__get__(self)
        self.test_code_action_info = test_code_action_info.__get__(self)
        self.test_code_street_info = test_code_street_info.__get__(self)
        self.test_code_showdown_info = test_code_showdown_info.__get__(self)
        self.test_code_pot_award_info = test_code_pot_award_info.__get__(self)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                     STREET                                                                       #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _prep_preFlop(self, street_name : str) -> None:
        
        self._initialize_start_order(street_name)
        # SB와 BB의 블라인드 포스팅은 bet으로 간주
        self.attack_flag == True
        self._posting_blind(street_name)

        # 시스템 로그. 유저 액션 기록
        self.log_hand_actions[street_name].append(("SB", {"bet" : self.SB}))
        self.log_hand_actions[street_name].append(("BB", {"bet" : self.BB}))
        
        self.players['SB']["actions"][street_name]["betting_size_total"]['bet'].append(self.SB)
        self.players['SB']["actions"][street_name]['pot_contribution']['bet'].append(self.SB) 
        self.players['SB']["actions"][street_name]["action_list"].append('bet')
        self.players['BB']["actions"][street_name]["betting_size_total"]['bet'].append(self.BB)
        self.players['BB']["actions"][street_name]['pot_contribution']['bet'].append(self.BB) 
        self.players['BB']["actions"][street_name]["action_list"].append('bet')    

        '''
        서버 요청 사항
        1. 현재 접속 중인 클라이언트의 유저 아이디 리스트 요청. on_user_list 변수에 할당
        2. 모든 클라이언트에게 스타팅 카드 전송 후 렌더링. users_starting_cards 딕셔너리 전달
        3. 모든 클라이언트에게 스택사이즈 렌더링 요청. users_stack_size 딕셔너리 전달
        4. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링. start_order 리스트 전달
        '''
        # on_user_list =  # 서버에서 전달 받은 현재 접속 중인 클라이언트들의 유저 아이디 리스트

        # 현재 접속 중인 유저만 남기고 start_order 재정렬
        # self._check_connection(on_user_list) # 실제코드

        users_starting_cards = dict()
        users_stack_size = dict()

        for position in self.start_order:
            starting_cards = self.players[position]['starting_cards']
            users_starting_cards[position] = starting_cards
            stack_size = self.players[position]['stk_size']
            users_stack_size[position] = stack_size

        start_order = self.start_order.copy() 

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    def _prep_street(self, street_name : str ) -> None:
        
        # 이전 스트릿에서 넘어온 유저만을 대상으로 start_order 재정렬
        self._initialize_start_order(street_name)

        # 스트릿에서 사용할 인스턴스 변수들 초기화
        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()

        '''
        서버 요청 사항
        1. 현재 접속 중인 클라이언트의 유저 아이디 리스트 요청. on_user_list 변수에 할당
        2. 모든 클라이언트에게 스타팅 카드 전송 후 렌더링. users_starting_cards 딕셔너리 전달
        3. 모든 클라이언트에게 커뮤니티 카드 전송 후 렌더링.community_cards 리스트 전달
        4. 모든 클라이언트에게 스택사이즈 렌더링 요청. users_stack_size 딕셔너리 전달
        5. 모든 클라이언트에게 팟 사이즈 렌더링 요청.  main_pot 전달
        6. start_order 에 있는 유저만 남기고 나머지 유저들 삭제 렌더링. start_order 리스트 전달
        '''

        # on_user_list =  # 서버에서 전달 받은 현재 접속 중인 클라이언트들의 유저 아이디 리스트

        # 현재 접속 중인 유저만 남기고 start_order 재정렬
        # self._check_connection(on_user_list) # 실제코드

        community_cards :list = self._face_up_community_cards(street_name)
        users_starting_cards = dict()
        users_stack_size = dict()

        for position in self.start_order:
            starting_cards = self.players[position]['starting_cards']
            users_starting_cards[position] = starting_cards
            stack_size = self.players[position]['stk_size']
            users_stack_size[position] = stack_size

        main_pot = self.pot_total

        start_order = self.start_order.copy() 

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    def _play_street(self, street_name : str ) -> None:

        while self.action_queue:

            current_player = self.action_queue[0]
            possible_actions : list = self._possible_actions(street_name, current_player)

            '''
            서버 요청 사항 
            시간제한은 클라이언트 쪽에서 구현
            1. current_player에 해당하는 클라이언트에게 possible_actions 리스트 전달, 렌더링 요청
            2. current_player에 해당하는 클라이언트가 bet, raise, all-in을 할 수 있는 경우 betting_condition 리스트 전달, 렌더링 요청
                self.prev_VALID 유저가 베팅 액션 선택시 베팅 해야하는 최소 금액
                self.prev_TOTAL 유저가 레이즈 액션 선택시 가능한 레이즈 최소 금액 렌더링 요청
            
            '''
            for action in possible_actions:
                if action in ['bet', 'raise', 'all-in']:
                    betting_condition = [self.prev_VALID, self.prev_TOTAL]

            stack_size = self.players[current_player]['stk_size']

            '''
            서버 응답 대기
            현재 액션할 차례인 클라이언트가 서버에 전달한 액션 내용을 서버로부터 받음
            응답 형식 : 딕셔너리 = {액션종류, 베팅금액}
            {'call' : None}, {'fold' : None}, {'check' : None},  {'all-in' : None} 
            {'bet' : bet_amount}, {'raise' : raise_amount} 
            서버로부터 받은 응답을 answer 변수에 할당
            '''

            # answer = 서버로부터 전달받은 유저의 액션 내용이 담긴 딕셔너리 

            # 테스트 코드
            answer = self.test_code_action_info(current_player, possible_actions, street_name)
            answer = self.just_get_input()

            # 클라이언트에게 전달 받은 응답이 call 이면
            if next(iter(answer)) == "call":
                self._call(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 fold 면 
            elif next(iter(answer)) == "fold":
                self._fold(street_name, current_player)
                
            # 클라이언트에게 전달 받은 응답이 check 면      
            elif next(iter(answer)) == "check":  # BB 만 가능
                self._check(street_name, current_player)

             # 클라이언트로부터 전달 받은 응답이 answer = {"bet" : bet_amount} 이면
            elif next(iter(answer)) == "bet": # 플롭부터 가능
                self._bet(street_name, current_player, answer)

            # 클라이언트로부터 전달 받은 응답이 answer = {"raise" : raised_total} 이면
            elif next(iter(answer)) == "raise":
                self._raise(street_name, current_player, answer)
                 
            # 클라이언트로부터 전달 받은 응답이 answer = {"all-in" : all_in_amount} 이면
            elif next(iter(answer)) == "all-in":
                self._all_in(street_name, current_player)

            '''
            서버 요청 사항
            1. 모든 클라이언트에게 answer 딕셔너리 전달
                현재 플레이어의 액션 종류 렌더링 요청
                각 액션에 따른 팟 금액 변화, 해당 유저의 스택사이즈 변화 렌더링 요청
            '''
            
            # 다음 차례 유저 액션큐 등록
            if self.start_order:
                self.action_queue.append(self.start_order.popleft())
            
            # 시스템 로그. 유저 액션 기록
            if next(iter(answer)) == 'all-in':
                answer = {'all-in' : self.players[current_player]['actions'][street_name]['betting_size_total']['all-in'][-1]}
                self.log_hand_actions[street_name].append((current_player, answer)) 
            elif next(iter(answer)) == 'call':
                answer = {'call' : self.players[current_player]['actions'][street_name]['betting_size_total']['call'][-1]}
                self.log_hand_actions[street_name].append((current_player, answer))
            else:
                self.log_hand_actions[street_name].append((current_player, answer)) 

    def _finishing_street(self, street_name : str ) -> None:

        # 사이드팟 생성
        pots = self._side_pots(street_name)
        self.side_pots[street_name]['pots'] = pots

        # 현재 스트릿의 올인 유저 리스트를 전체 올인 리스트에 추가
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name
       # 현재 스트릿의 폴드 유저 리스트를 전체 폴드 리스트에 추가
        for position in self.fold_users:
            self.fold_users_total[position] = street_name

        # 다음 스트릿으로 넘어가는 유저 목록
        self.survivors.extend(list(self.actioned_queue))

        # 테스트 코드
        self.test_code_street_info(street_name)
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    SHOWDOWN                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
       
    def _end_conditions(self, street_name : str ) -> bool:
        
        if len(self.fold_users_total) == self.rings:
            print("every user fold")
            return 

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 수도 있고, 마지막 베팅 유저일 수도 있다.
        if len(self.fold_users_total) == self.rings - 1 or len(self.actioned_queue) == 1 :
            if self.actioned_queue and self.check_users:
                self.check_users[0] == self.actioned_queue[0]
                print("all other user fold after first player check")
                return
            
            # 마지막 남은 유저 1명이 올인 유저인 경우
            if (len(self.all_in_users_total) == 1 and self.all_in_users):
                self.table_card_open_first = True
                self.table_card_open_only = True                
                return True
            
            # 마지막 남은 유저 1명이 올인 유저가 아닌 베팅 유저인 경우
            if not self.all_in_users_total and self.actioned_queue:
                self.table_card_open_first = True
                self.table_card_open_only = True
                return True
        
        # 올인에 콜할수 있는 유저가 1명 뿐인 경우
        if self.short_stack_end_flag:
            return True

        # 모두 올인 또는 한명 빼고 전부 올인한 경우
        if self.rings - 1 <= len(self.all_in_users_total) + len(self.fold_users_total):
            return True
        
        # 현재 스트릿이 리버인 경우
        if street_name == 'river':
            if len(self.actioned_queue) == len(self.check_users):
                self.river_all_check = True
            if len(self.check_users) == 0:
                self.river_bet_exists = True
                if len(self.fold_users_total) == self.rings - 1:
                    self.table_card_open_only = True
            return True
        
        return False
    
    def _showdown(self, street_name : str) -> dict:
        # 커뮤니티 카드 오픈 순서
        def _community_cards_open_order(street_name) -> list:
            stages = {
                'pre_flop': [("burned", 0), "flop", ("burned", 1), "turn", ("burned", 2), "river"],
                'flop': [("burned", 1), "turn", ("burned", 2), "river"],
                'turn': [("burned", 2), "river"],
                'river': []
            }
            open_order = []
            for stage in stages.get(street_name, []):
                if isinstance(stage, tuple):
                    open_order.append(self.log_community_cards[stage[0]][stage[1]])
                else:
                    open_order.append(self.log_community_cards[stage])
            return open_order
        
        community_cards : list = self._face_up_community_cards_for_showdown(street_name) # _face_up_community_cards_for_showdown 호출 후
        community_cards_open_order : list = _community_cards_open_order(street_name) #_community_cards_open_order 호출되어야 한다. 호출순서 바뀌면 안됨
        # self._check_connection(on_user_list) # 실제코드
        user_cards : dict = self._face_up_user_hand()
        nuts = self._compare_hand(user_cards, community_cards)
        
        if self.user_card_open_first:
            '''
            서버에 요청
            모든 클라이언트에게 동시에 스타팅 카드 오픈 렌더링 후
            커뮤니티 카드 오픈 렌더링 요청
            user_cards
            community_cards_open_order
            위 변수를 인자로 전달
            '''
            pass
        elif self.table_card_open_first and street_name != 'river':
            if self.table_card_open_only:
                pass
                '''
                서버에 요청
                모든 클라이언트에 커뮤니티 카드 오픈 렌더링 
                community_cards_open_order
                위 변수를 인자로 전달
                '''
            pass
            '''
            서버에 요청
            모든 클라이언트에 커뮤니티 카드 오픈 렌더링 후
            유저의 스타팅 카드 액션 순서대로 오픈 렌더링 요청
            users
            actioned_queue
            community_cards_open_order
            위 변수를 인자로 전달
            '''
        elif street_name == 'river':
            if self.river_all_check:
                pass
                '''
                서버에 요청
                리버에서 체크했던 순서대로 클라이언트 카드 오픈
                self.check_users 
                위 변수를 인자로 전달
                '''
            elif self.river_bet_exists and self.table_card_open_only:
                pass
                '''
                카드 오픈과 관련해 아무것도 렌더링하지 않음
                '''
            elif self.river_bet_exists and not self.table_card_open_only:
                pass
                '''
                서버에 요청
                리버에서 마지막으로 베팅액션을 한 클라이언트부터 딜링 방향으로 카드 오픈
                self.survivors 
                위 변수를 인자로 전달
                '''
            pass

        return nuts

    def _pot_award(self, nuts : dict, street_name : str, version : int) -> None:

        if version == 1:
            self._pot_award_1(nuts, street_name)

        elif version == 2:
            self._pot_award_2(nuts, street_name)
        
        elif version == 3:
            self._pot_award_3(nuts, street_name)


    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      HAND                                                                        #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _preFlop(self, stk_size : list) -> None:
        
        street_name = "pre_flop"
        self._prep_preFlop(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(nuts, street_name, 2)
            
            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._flop(stk_size)
    
    def _flop(self, stk_size : list) -> None:
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(nuts, street_name, 1)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._turn(stk_size)
    
    def _turn(self, stk_size : list) -> None:

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(nuts, street_name, 1)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._river(stk_size)
    
    def _river(self, stk_size : list) -> None:

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            self.test_code_showdown_info()

            self._pot_award(nuts, street_name, 1)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            raise SystemExit("!!!!!!!!!!!!!!종료조건에 걸리지 않는 상황입니다. 유저들의 액션을 검토해서 종료조건을 수정하거나 추가하세요!!!!!!!!!!!!!!")

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    EXECUTION                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def go_street(self, stk_size : list) -> None:
        self._preFlop(stk_size)     
