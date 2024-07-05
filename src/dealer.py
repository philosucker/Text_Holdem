from src import Base
from collections import deque, OrderedDict, defaultdict
import sys

rings = 6  # robby 에서 전달 받음
user_id_list = ['1', '2', '3', '4', '5', '6'] # robby 에서 전달 받음
stakes = "low"   # robby 에서 전달 받음
stk_size = {'1' : 100, '2' : 100, '3' : 100, '4' : 100, '5' : 100, '6' : 100}  # SQL DB에서 전달 받음


class Dealer(Base):

    def __init__(self, user_id_list, stk_size, rings, stakes):
        super().__init__(user_id_list, stk_size, rings, stakes)

        if self.rings == 6:
            self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
            
        elif self.rings == 9:
            self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])

        self.all_in_users_total = OrderedDict()
        self.fold_users = []

        self.main_pot_cumulative = 0
        self.pot_change = [self.main_pot_cumulative]
        self.side_pot = False # 모든 스트릿 포함 최초 올인 발생시 True
        self.main_pot_confirmed = defaultdict(dict)

        # 필요한 키들을 수동으로 설정합니다.
        self.main_pot_confirmed["pre_flop"] = {}
        self.main_pot_confirmed["flop"] = {}
        self.main_pot_confirmed["turn"] = {}
        self.main_pot_confirmed["river"] = {}
        
        self.street_name = ["pre_flop", "flop", "turn", "river"]

        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()      

    def _initialize_betting_state(self):
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신

        self.LPFB = self.BB # the largest prior full bet = the last legal increment = minimum raise
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

        self.street_pot = 0 # 해당 스트릿에서만 발생한 베팅 총액

    def _initialize_action_state(self):
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = list()
        
        self.check_users = list()
        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제. 구현 필요
        self.reorder_flag = True # 현재 액션 유저를 기준으로 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

    def _initialize_conditions(self):
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건

        self.winner_confirmed = False
        self.user_card_open_first = False # TDA Rule 16 : Face Up for All
        self.table_card_open_first = False
        self.table_card_open_only = False # TDA Rule 18 : Asking to See a Hand

        self.river_all_check = False
        self.river_bet_exists = False

        self.survivors = list() # 다음 스트릿으로 갈 생존자 리스트

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      ACTION                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _possible_actions(self, street_name, current_player):

        player_stack = self.players[current_player]['stk_size']

        if street_name == 'pre_flop':
            # 프리플롭에서 첫 바퀴를 돌고 BB 차례가 되었을 때, 모두 콜 or 폴드만 한 경우 BB option 및 check 구현
            if self.raised_total == 0 and len(self.all_in_users) == 0 and current_player == 'BB':
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["check", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in : after first all-in, under call
            else:
                if self.prev_TOTAL <= player_stack:
                    possible_actions = ["call", "raise", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in
        else:
            if not self.attack_flag:  # not attacked
                if self.prev_VALID <= player_stack:
                    possible_actions = ["bet", "check", "fold", "all-in"]
                elif player_stack < self.prev_VALID:
                    possible_actions = ["check", "fold", "all-in"] # short-all-in : under bet
            elif self.attack_flag:  # attacked
                if self.prev_TOTAL <= player_stack:
                    if self.raise_counter <= 5:
                        possible_actions = ["call", "raise", "fold", "all-in"]
                    else:
                        possible_actions = ["call", "fold", "all-in"]
                elif self.prev_VALID <= player_stack < self.prev_TOTAL:
                    possible_actions = ["call", "fold", "all-in"] # short-all-in : after first all-in, under call
                elif player_stack < self.prev_VALID:
                    possible_actions = ["fold", "all-in"] # short-all-in : after first all-in, under call

        return possible_actions
       
    def _bet(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        # bet_amount : 클라이언트에게서 전달받은 베팅액수
        self.bet_amount = answer['bet']

        self.LPFB = self.bet_amount
        self.prev_VALID = self.bet_amount
        self.prev_TOTAL = self.prev_VALID + self.LPFB

        # bet은 항상 첫번째 액션
        self.players[current_player]["stk_size"] -= self.bet_amount # 스택사이즈 업데이트
        self.main_pot_cumulative += self.bet_amount # 메인팟 업데이트
        
        self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size_total["bet"].append(self.prev_VALID)
        pot_contribution["bet"].append(self.prev_VALID)
        action_list.append("bet")

        self.attack_flag = True 

        # 액션큐 처리. 벳의 경우 자기 앞에 액션은 체크를 한 사람 밖에 없다.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        베팅한 클라이언트의 스택 사이즈를 self.bet_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.bet_amount을 더한 결과로 렌더링
        '''
    
    def _call(self, street_name, current_player):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        # 현재 액션이 첫번째 액션이 아닌 경우
        if action_list:
            last_action = action_list[-1]
        # 현재 액션 콜이 첫번째 액션인 경우
        else:
            last_action = None

        # 현재 스트리트가 프리플롭이거나 (모든 스트리트에서 현재 액션이 첫 액션이 아니고 마지막 액션이 체크가 아닌 경우)
        if street_name == 'pre_flop' or (action_list and last_action != 'check'):
            if last_action:
                call_amount = self.prev_VALID - betting_size_total[last_action][-1]
            else:
                call_amount = self.prev_VALID

        # 현재 스트리트가 프리플롭이 아니고 (액션리스트가 비어있거나 마지막 액션이 체크인 경우) 
        # 플롭, 턴, 리버에서 현재 액션 콜이 첫 액션인 경우 또는 첫 액션이 체크였고 자기 차례로 돌아와 콜을 한 경우
        else:
            call_amount = self.prev_VALID
            
        self.players[current_player]["stk_size"] -= call_amount # 스택사이즈 업데이트
        self.main_pot_cumulative += call_amount # 메인팟 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size_total["call"].append(self.prev_VALID)
        pot_contribution["call"].append(call_amount)
        action_list.append("call")

        self.actioned_queue.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        콜한 클라이언트의 스택 사이즈를 self.prev_VALID 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 prev_VALID을 더한 결과로 렌더링
        '''

    def _raise(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        # raised_total : 클라이언트에게서 전달받은 레이즈 액수 (레이즈 액수는 total을 의미)
        self.raised_total = answer["raise"]

        self.LPFB = self.raised_total - self.prev_VALID
        self.prev_VALID = self.raised_total
        self.prev_TOTAL = self.LPFB + self.prev_VALID

        # 현재 액션이 첫번째 액션이 아니고, 마지막으로 한 액션이 check가 아닌 경우
            # 모든 스트릿에서 자신이 현재 레이즈 액션 이전에 벳 or 레이즈 or 콜을 했었고 
            # 이후 올인이나 레이즈가 일어나서 다시 자기 차례에 레이즈를 한 경우        
        if action_list and action_list[-1] != 'check':
            last_action = action_list[-1]
            raise_amount = self.raised_total - betting_size_total[last_action][-1]
        # 플롭, 턴, 리버에서 자신이 체크 레이즈를 하는 경우
        else:
            raise_amount = self.raised_total

        self.players[current_player]["stk_size"] -= raise_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += raise_amount # 메인 팟 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
        self.street_pot += self.prev_VALID

        # 로그 업데이트
        betting_size_total["raise"].append(self.prev_VALID)
        pot_contribution["raise"].append(raise_amount)
        action_list.append("raise")

        self.attack_flag = True
        
        self.raise_counter += 1

        # 액션큐 처리
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        self.actioned_queue.append(self.action_queue.popleft())
        
        '''
        모든 클라이언트들에게 다음을 요청
        레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 raised_total을 더한 결과로 렌더링
        '''
    
    def _all_in(self, street_name, current_player, answer):

        if current_player in self.check_users:
            self.check_users.remove(current_player)

        betting_size_total = self.players[current_player]["actions"][street_name]["betting_size_total"]
        pot_contribution = self.players[current_player]["actions"][street_name]["pot_contribution"]        
        action_list = self.players[current_player]["actions"][street_name]["action_list"]

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트에게 올인 버튼 렌더링(지속형 이벤트)
        '''
        # all_in_amount : 클라이언트에게서 전달받은 올인액수 (total을 의미)
        self.all_in_amount = self.players[current_player]['stk_size']

        # 해당 올인이 open-bet인 경우
        if not self.attack_flag: 
            if self.prev_VALID <= self.all_in_amount:
                self.LPFB = self.all_in_amount
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False
        # 해당 올인이 open-bet이 아닌 경우
        else:   
            if self.prev_TOTAL <= self.all_in_amount:
                self.LPFB = self.all_in_amount- self.prev_VALID
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.prev_VALID <= self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            elif self.all_in_amount < self.prev_VALID:
                self.reorder_flag = False

        self.players[current_player]["stk_size"] -= self.all_in_amount # 스택 사이즈 업데이트
        self.main_pot_cumulative += self.all_in_amount # 메인팟 업데이트
      
        self.pot_change.append(self.all_in_amount)  # 팟 변화량 업데이트
        self.street_pot += self.all_in_amount

        # 로그 업데이트
        betting_size_total["all-in"].append(self.all_in_amount)
        pot_contribution["all-in"].append(self.all_in_amount)
        action_list.append("all-in")
    
        self.attack_flag = True
        self.user_card_open_first = True
        self.side_pot = True

        # 액션큐 처리
        if self.reorder_flag and self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        # 현재 올인 금액이 언더콜인 경우 start_order 유지
        elif not self.reorder_flag:
            self.reorder_flag = True

        self.all_in_users.append(self.action_queue.popleft())

        '''
        모든 클라이언트들에게 다음을 요청
        올인한 클라이언트의 스택 사이즈를 self.all_in_amount 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 self.all_in_amount을 더한 결과로 렌더링
        '''

        # 딥스택 유저 수 부족으로 인한 핸드 종료조건
        for position in self.start_order:
            if self.prev_VALID <= self.players[position]['stk_size']:
                self.deep_stack_user_counter += 1

        # 첫 올인에 이 조건이 걸리는 건 게임 진행시간 단축에 의미있음
        # 올인유저 제외 start_order에 남은 인원이 1명 일때 이 조건이 걸리면
        # _end_conditions 에서 (모두 올인 또는 한명빼고 전부올인) 종료조건과 동일한 조건이 됨  
        if self.deep_stack_user_counter < 2:
            self.short_stack_end_flag == True
        
    def _update_pot(self, street_name):
        # 각 스트릿에서의 첫 베팅부터 합산한 팟 크기와 현재 스트리트까지의 팟 총액
        self.main_pot_confirmed[street_name][street_name] = self.main_pot_cumulative

    def _multi_pots(self, street_name):  # 사이드팟 생성함수

        all_user : list = list(self.actioned_queue) + self.all_in_users + self.fold_users

        # 한 명 빼고 모두 폴드한 경우 이 때 남은 한명이 올인유저일 경우
        if len(self.all_in_users) == 1 and len(self.fold_users) == self.rings - 1:
            # 그런 올인 유저가 프리플롭에서 발생했을 때 그의 지분은 블라인드
            if street_name == "pre_flop":
                self.main_pot_confirmed[street_name][self.all_in_users[0]] = self.SB + self.BB
                self.players[self.all_in_users[0]]['stk_size'] += self.all_in_amount
                self.main_pot_cumulative -= self.all_in_amount
            # 그런 올인 유저가 플롭이후부터 발생했을 때 그의 유저의 지분은 직전 스트릿까지의 팟 총액
            else:
                prev_street = self.street_name[self.street_name.index(street_name) - 1]
                prev_whole_pot = self.main_pot_confirmed[prev_street][prev_street]
                self.main_pot_confirmed[street_name][self.all_in_users[0]] += prev_whole_pot
                self.players[self.all_in_users[0]]['stk_size'] += self.all_in_amount
                self.main_pot_cumulative -= self.all_in_amount
        else:
            def sum_pot_contributions(path):
                pot_contribution = path["pot_contribution"]
                total_sum = 0
                for key in pot_contribution:
                    total_sum += sum(pot_contribution[key])
                return total_sum
            
            for all_in_position in self.all_in_users:
                self.main_pot_confirmed[street_name][all_in_position] = 0
                for position in all_user:
                    path = self.players[position]["actions"][street_name]
                    # 개별 올인 유저의 "해당 스트릿에서의" 메인팟에 대한 지분
                    stake = sum_pot_contributions(path)
                    self.main_pot_confirmed[street_name][all_in_position] += stake
                    # 플롭 이후 스트릿에서 올인을 했다면, 그의 지분은 그 스트릿에서의 자기 올인에 대한 지분에 직전 스트릿까지의 팟 총액을 더해야 한다.
                if street_name != "pre_flop":
                    prev_street = self.street_name[self.street_name.index(street_name) - 1]
                    prev_pot_cumulative = self.main_pot_confirmed[prev_street][prev_street]
                    self.main_pot_confirmed[street_name][all_in_position] += prev_pot_cumulative
        
    def _check(self, street_name, current_player):
        last_action = "check"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.actioned_queue.append(current_player)
        self.check_users.append(self.action_queue.popleft())
        '''
        모든 클라이언트들에게 다음을 요청
        체크한 플레이어가 체크했음을 렌더링       
        '''
    
    def _fold(self, street_name, current_player):

        if current_player in self.check_users: # 체크했던 유저가 폴드할 수도 있다.
            self.check_users.remove(current_player)

        last_action = "fold"
        self.players[current_player]["actions"][street_name]["action_list"].append(last_action)
        self.fold_users.append(self.action_queue.popleft())

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    SHOWDOWN                                                                      #
    ####################################################################################################################################################
    ####################################################################################################################################################
       
    def _end_conditions(self, street_name):
        
        if len(self.fold_users) == self.rings:
            print("every user fold")
            return 

        # 한 명 빼고 모두 폴드한 경우 = 액션을 마친 유저 숫자가 1명 뿐인 경우
        # 이 때 남은 한명은 올인유저일 수도 있고, 마지막 베팅 유저일 수도 있다.
        if len(self.fold_users) == self.rings - 1 or len(self.actioned_queue) == 1 :
            if self.actioned_queue and self.check_users:
                self.check_users[0] == self.actioned_queue[0]
                print("all other user fold after first player check")
                return
            
            # 마지막 남은 유저 1명이 올인 유저인 경우
            if (len(self.all_in_users_total) == 1 and self.all_in_users):
                self.winner_confirmed = True
                self.user_card_open_first = False
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
            self.winner_confirmed = True
            return True

        # 모두 올인 또는 한명 빼고 전부 올인한 경우
        if self.rings - 1 <= len(self.all_in_users_total) + len(self.fold_users):
            return True
        
        # 현재 스트릿이 리버인 경우
        if street_name == 'river':
            if not self.user_card_open_first:
                self.table_card_open_first = True
            
            self.river_all_check = True
            self.river_bet_exists = True
            return True
        

        return False
    
    def _compare_hand(self, user_cards : dict, community_cards : list) -> dict:

        for position in user_cards:
            pocket_cards = user_cards[position]
            best_hands = self._make_best_hands(pocket_cards, community_cards)
            self.log_best_hands[position] = best_hands

        best_rank = 0
        nuts_positions = []

        # 각 위치별로 최고의 핸드를 검색
        for position, best_hands_dict in self.log_best_hands.items():
            # 현재 위치의 가장 높은 랭크와 해당 핸드를 검색
            highest_rank, hand = max(best_hands_dict.items(), key=lambda item: self.hand_power.get(item[0], 0))
            current_rank = self.hand_power.get(highest_rank, 0)
            
            # 현재 랭크가 가장 높은 랭크보다 높으면 업데이트
            if current_rank > best_rank:
                best_rank = current_rank
                nuts_positions = [position]
            # 현재 랭크가 가장 높은 랭크와 같으면 위치 추가
            elif current_rank == best_rank:
                nuts_positions.append(position)

        # 타이가 발생하는 경우 카드 랭크와 키커로 넛츠 판별. 무승부시 복수 넛츠 허용
        if len(nuts_positions) > 1:
            final_nuts_positions = self._resolve_ties(nuts_positions)
            nuts_positions = final_nuts_positions

        for position in nuts_positions:
            self.log_nuts[position] = self.log_best_hands[position]

        # 유저의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        users_ranking = self._users_ranking()

        return users_ranking

    def _showdown(self, street_name):
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
                    open_order.append(self.log_hand_cards[stage[0]][stage[1]])
                else:
                    open_order.append(self.log_hand_cards[stage])
            return open_order

        community_cards : list = self._face_up_community_cards_for_showdown(street_name)
        user_cards : dict = self._face_up_user_hand()
        users_ranking : list = self._compare_hand(user_cards, community_cards)
        community_cards_open_order : list = _community_cards_open_order(street_name)

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
        elif self.table_card_open_first and street_name == 'river':
            if self.river_all_check:
                pass
                '''
                서버에 요청
                리버에서 체크했던 순서대로 클라이언트 카드 오픈
                TDA Rule 7:Non All-In Showdowns and Showdown Order
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
                TDA Rule 7:Non All-In Showdowns and Showdown Order
                '''
            pass

        return users_ranking

    # def _pot_award(self, street_name, users_ranking):
        '''
        TDA Rule 20: Awarding Odd Chips
        팟 분배후 칩이 남는 경우
        하이 핸드 또는 로우 핸드가 두 개 이상인 경우 : 나머지 칩은 버튼에서 왼쪽으로 가장 가까운 플레이어에게 수여
        하이/로우 스플릿의 경우 : 전체 팟이 홀수인 경우 나머지 칩은 하이 팟에 넣는다
        '''
        '''
        self.side_pot = True
        self.winner_confirmed = True
        위 두가지 변수만 고려
        users_ranking 에는 all_in_users_total + actioned_queue 의 유저들의 베스트 핸드를 비교해 
        내림차순으로 정렬한 유저 포지션 리스트가 들어 있다. 무승부인 포지션은 튜플로 묶여 있다.
        넛츠는 self.log_nuts 에 있다. 타이인 경우 동률인 포지션 이름이 모두 들어 있다.
        '''
        winner_list = [position for position in self.log_nuts]

        if len(winner_list) == 1:
            winner = winner_list[0]
            # 승자가 현재 스트릿이 아닌 이전 스트릿의 올인 유저였을 경우 그의 팟 지분을 분배
            if winner in self.all_in_users_total and self.all_in_users_total[winner] != street_name:
                street = self.all_in_users_total[winner]
                stake = self.main_pot_confirmed[street][winner]
                self.players[winner]['stk_size'] += stake
                self.main_pot_cumulative -= stake

                # 남은 팟을 users_ranking을 사용해 분배
                while self.main_pot_cumulative:
                    users_ranking[1:] 
            
            # 승자가 현재 스트릿의 올인 유저이거나 한번도 올인한 적 없이 끝까지 살아남은 유저였을 때
            elif winner in self.all_in_users or winner not in self.all_in_users_total:
                action_list = self.players[winner]["actions"][street_name]["action_list"]
                betting_size_total = self.players[winner]["actions"][street_name]["betting_size_total"]
                last_action = action_list[-1]
                stake = betting_size_total[last_action][-1]
                self.players[winner]['stk_size'] += stake
                self.main_pot_cumulative -= stake

        elif len(winner_list) > 1:
            users_ranking[1:]
            # 남은 팟을 users_ranking을 사용해 분배
            pass 

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    AUXILIARY                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _posting_blind(self):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"]["pre_flop"]["betting_size_total"]["bet"].append(self.SB)
            self.players["SB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.players["BB"]["actions"]["pre_flop"]["betting_size_total"]["bet"].append(self.BB)
            self.players["BB"]["actions"]["pre_flop"]["action_list"].append("bet")
            self.main_pot_cumulative += (self.SB + self.BB)
            self.street_pot += (self.SB + self.BB)

    def _check_connection(self, on_user_list):
        connected_users = []
        if on_user_list:
            for on_user in on_user_list:
                connected_users.append(self.user2pos[on_user])
            for position in self.start_order:
                if position not in connected_users:
                    self.fold_users.append(self.start_order.popleft())   

    def _reorder_start_member(self):
        if self.rings == 6:
            start_order = deque(["SB", "BB", "UTG", "HJ", "CO", "D"])
        elif self.rings == 6:
            start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])     
        new_order = []
        while start_order:
            position = start_order.popleft()
            if position in self.survivors:
                new_order.append(position)
        
        self.start_order = deque(new_order)

    def _face_up_community_cards(self, street_name : str) -> list: 
        self.log_hand_cards['burned'].append(self.stub.pop(0)) # 버닝
        if street_name == 'flop':
            for _ in range(3):
                self.log_hand_cards[street_name].append(self.stub.pop(0))
        else:
            self.log_hand_cards[street_name].append(self.stub.pop(0))

        return self.log_hand_cards[street_name]
    
    def _face_up_community_cards_for_showdown(self, street_name :str) -> list :

        if street_name == 'pre_flop':
            self._face_up_community_cards('flop')
            self._face_up_community_cards('turn')
            self._face_up_community_cards('river')
        elif street_name == 'flop':
            self._face_up_community_cards('turn')
            self._face_up_community_cards('river')
        elif street_name == 'turn':
            self._face_up_community_cards('river')

        self.log_hand_cards["table_cards"] = self.log_hand_cards["flop"] + self.log_hand_cards["turn"] + self.log_hand_cards["river"]
        community_cards: list = self.log_hand_cards["table_cards"]

        return community_cards
    
    def _face_up_user_hand(self):
        user_hand = dict()
        all_user = [position for position in self.all_in_users_total] + list(self.actioned_queue)
        for position in all_user:
            starting_cards = self.players[position]['starting_cards']
            user_hand[position] = starting_cards
        return user_hand
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                     STREET                                                                       #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _prep_preFlop(self):

        # SB와 BB의 블라인드 포스팅은 bet으로 간주
        self.attack_flag == True
        self._posting_blind()

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

    def _prep_street(self, street_name):
        
        # 이전 스트릿에서 넘어온 유저만을 대상으로 start_order 재정렬
        self._reorder_start_member()

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

        main_pot = self.main_pot_cumulative

        start_order = self.start_order.copy() 

        # 유저 액선큐 등록
        if self.start_order:
            self.action_queue.append(self.start_order.popleft())

    def _play_street(self, street_name):

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
            answer = self.test_code_action_info(current_player, possible_actions)

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
                self._all_in(street_name, current_player, answer)

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
            self.log_hand_actions[street_name].append((current_player, answer)) 

    def _finishing_street(self, street_name):

        # 해당 스트릿까지의 팟 누적합 업데이트
        self._update_pot(street_name)

        # 해당 스트릿에서 올인 유저 발생시 올인 유저의 지분 계산 (사이드 팟 생성)
        if self.all_in_users:
            self._multi_pots(street_name)

        # 현재 스트릿의 올인 유저 리스트를 전체 올인 리스트에 추가
        for position in self.all_in_users:
            self.all_in_users_total[position] = street_name

        # 스택 사이즈가 0인 유저는 actioned_queue에서 제외 
        # 해당 스트릿 종료시 마지막 액션이 콜인 유저의 스택사이즈가 0이 되는 경우가 있음. 케이스 참고
        if self.actioned_queue:
            new_actioned_queue = []
            for position in self.actioned_queue:
                if self.players[position]['stk_size'] == 0:
                    continue
                else:
                    # 다음 스트릿으로 이동시킬 유저 리스트 업데이트
                    new_actioned_queue.append(position)
            self.survivors.extend(new_actioned_queue)

        # 테스트 코드
        self.test_code_street_info(street_name)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      HAND                                                                        #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _preFlop(self):
        
        street_name = "pre_flop"
        self._prep_preFlop()
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            # self._pot_award(users_ranking)

            # 테스트 코드
            self.test_code_showdown_pot_award_info
        else:
            self._flop()
    
    def _flop(self):
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            # self._pot_award(users_ranking)

            # 테스트 코드
            self.test_code_showdown_pot_award_info
        else:
            self._turn()
    
    def _turn(self):

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            # self._pot_award(users_ranking)

            # 테스트 코드
            self.test_code_showdown_pot_award_info
        else:
            self._river()
    
    def _river(self):

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            users_ranking = self._showdown(street_name)
            # self._pot_award(users_ranking)

            # 테스트 코드
            self.test_code_showdown_pot_award_info
        else:
            print("!!!!!!!!!!!!!!종료조건에 걸리지 않는 상황입니다. 유저들의 액션을 검토해서 종료조건을 수정하거나 추가하세요!!!!!!!!!!!!!!")    

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    EXECUTION                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def go_street(self):
        self._preFlop()     

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    TEST CODE                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def get_input(self, prompt):
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
    
    def test_code_action_info(self, current_player, possible_actions):
        stack_size = self.players[current_player]['stk_size']
        print(f'LPFB : {self.LPFB}')
        print(f'prev_VALID : {self.prev_VALID}')
        print(f'prev_TOTAL : {self.prev_TOTAL}')
        print(f'{current_player} 님의 현재 스택사이즈는 {stack_size}입니다')
        print(f'{current_player} 님의 가능한 액션은 {possible_actions} 입니다') 
        answer = self.get_input(f'{current_player} 님 액션을 입력해 주세요. ')    
        print(f'{current_player}님의 액션은 {next(iter(answer))} 입니다')
        print()
        return answer

    def test_code_street_info(self, street_name):
        print()
        print(f'{street_name} 스트리트')
        print(f'actioned_queue: {self.actioned_queue}')
        print(f'fold_users: {self.fold_users}')
        print(f'all_in_users: {self.all_in_users}')
        print(f'all_in_users_total: {self.all_in_users_total}')
        print()
        print(f'user actions and bettig size according to start order : {self.log_hand_actions}')
        print(f'main_pot_cumulative : {self.main_pot_cumulative}')
        print(f'main_pot_confirmed : {self.main_pot_confirmed}')
        print(f'생존자 : {self.survivors}')
        print()

    def test_code_showdown_pot_award_info(self):
        print(f'best hands : {self.log_best_hands}')
        print(f'users_ranking : {self.log_users_ranking}')
        print(f'nuts : {self.log_nuts}')
        print()
        print(f'main_pot : {self.main_pot_cumulative}')
        print()
        for position in self.players:
            stack_size = self.players[position]['stk_size']
            print(f'{position} 의 남은 stk_size : {stack_size}')

  






