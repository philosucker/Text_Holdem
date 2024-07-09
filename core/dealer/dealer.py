from src import Base
from collections import deque, OrderedDict, defaultdict
from itertools import combinations
import sys

class Dealer(Base):

    def __init__(self, user_id_list, stk_size, rings, stakes):
        super().__init__(user_id_list, stk_size, rings, stakes)

        self.start_order = None

        self.all_in_users_total = OrderedDict()
        self.fold_users_total = OrderedDict()

        self.pot_total = 0 # 팟 총액
        self.pot_change = [self.pot_total]

        self.side_pots = defaultdict(dict)
        self.side_pots["pre_flop"] = {}
        self.side_pots["flop"] = {}
        self.side_pots["turn"] = {}
        self.side_pots["river"] = {}

        self.street_name = ["pre_flop", "flop", "turn", "river"]

        self._initialize_betting_state()
        self._initialize_action_state()
        self._initialize_conditions()      

    def _initialize_betting_state(self):
        self.raised_total = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.bet_amount = 0 # 클라이언트로부터 전달받는 데이터, 전달 받을 때마다 갱신
        self.all_in_amount = 0   

        self.LPFB = self.BB # the largest prior full bet = the last legal increment = minimum raise
        self.prev_VALID = self.BB  # 콜시 유저의 스택에 남아 있어야 하는 최소 스택 사이즈의 기준
        self.prev_TOTAL = self.prev_VALID + self.LPFB # 레이즈시 유저의 스택에 남아있어야 하는 최소 스택 사이즈의 기준

    def _initialize_action_state(self):
        self.action_queue = deque([])
        self.actioned_queue = deque([])

        self.all_in_users = list()
        self.fold_users = list()
        self.check_users = list()

        self.attack_flag = False # only only and just once bet, raise, all-in is True  # 플롭부터는 False로 초기화
        self.raise_counter = 0 # 5가 되면 Possible action 에서 raise 삭제
        self.reorder_flag = True # 언더콜인 올인 발생시 actioned_queue에 있는 유저들을 start_order 리스트 뒤에 붙이는 reorder를 금지시키기 위한 플래그

    def _initialize_conditions(self):
        self.deep_stack_user_counter = 0
        self.short_stack_end_flag = False # 올인 발생시 딥스택 유저 수 부족으로 바로 핸드 종료시키는 조건

        self.user_card_open_first = False # TDA Rule 16 : Face Up for All
        self.table_card_open_first = False
        self.table_card_open_only = False # TDA Rule 18 : Asking to See a Hand

        self.river_all_check = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order
        self.river_bet_exists = False # TDA Rule : 17 : Non All-In Showdowns and Showdown Order

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
        self.pot_total += self.bet_amount # 팟총액 업데이트
        
        self.pot_change.append(self.prev_VALID) # 팟 변화량 업데이트

        # 로그 업데이트
        betting_size_total["bet"].append(self.prev_VALID)
        pot_contribution["bet"].append(self.prev_VALID)
        action_list.append("bet")

        self.attack_flag = True 


        # 현재 베팅 액션으로 인해 스택사이즈가 0이 되었다면 해당 베팅은 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())

        # 액션큐 처리. 벳의 경우 자기 앞에 액션은 체크를 한 사람 밖에 없다.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        
        if self.action_queue:
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
        self.pot_total += call_amount # 팟 총액 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트
 

        # 로그 업데이트
        betting_size_total["call"].append(self.prev_VALID)
        pot_contribution["call"].append(call_amount)
        action_list.append("call")

        # 현재 콜 액션으로 인해 스택사이즈가 0이 되었다면 해당 콜은 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())
        else:
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
        self.pot_total += raise_amount # 팟 총액 업데이트

        self.pot_change.append(self.prev_VALID)  # 팟 변화량 업데이트

        # 로그 업데이트
        betting_size_total["raise"].append(self.prev_VALID)
        pot_contribution["raise"].append(raise_amount)
        action_list.append("raise")

        self.attack_flag = True
        
        self.raise_counter += 1

        # 현재 레이즈 액션으로 인해 스택사이즈가 0이 되었다면 해당 레이즈는 올인으로 간주
        if self.players[current_player]["stk_size"] == 0:
            self.all_in_users.append(self.action_queue.popleft())

        # 액션큐 처리.
        if self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        
        if self.action_queue:
            self.actioned_queue.append(self.action_queue.popleft())
        
        '''
        모든 클라이언트들에게 다음을 요청
        레이즈한 클라이언트의 스택 사이즈를 raised_total 만큼 차감한 결과로 렌더링
        메인팟 사이즈를 raised_total을 더한 결과로 렌더링
        '''
    
    def _all_in(self, street_name, current_player):

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
            elif self.prev_VALID < self.all_in_amount < self.prev_TOTAL:
                self.prev_VALID = self.all_in_amount
                self.prev_TOTAL = self.prev_VALID + self.LPFB
            # 올인 금액이 현재 콜해야 하는 금액과 같다면 해당 올인은 콜로 간주
            elif self.all_in_amount <= self.prev_VALID:
                self.reorder_flag = False

        self.players[current_player]["stk_size"] -= self.all_in_amount # 스택 사이즈 업데이트
        self.pot_total += self.all_in_amount # 팟 총액 업데이트
      
        self.pot_change.append(self.all_in_amount)  # 팟 변화량 업데이트

        # 로그 업데이트
        betting_size_total["all-in"].append(self.all_in_amount)
        pot_contribution["all-in"].append(self.all_in_amount)
        action_list.append("all-in")
    
        self.attack_flag = True
        self.user_card_open_first = True

        # 액션큐 처리
        if self.reorder_flag and self.actioned_queue:
            self.start_order.extend(self.actioned_queue)
            self.actioned_queue.clear()
        # 현재 올인 금액이 언더콜인 경우 start_order 유지, reorder_flag 디폴트 값으로 변환
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

    def _individual_pot_contribution(self, path):
        pot_contribution = path
        total_sum = 0
        for key in pot_contribution:
            total_sum += sum(pot_contribution[key])

        return total_sum

    def _sum_individual_pot_contrbutions(self, street_name, user_list):
        users_stake = 0
        for user in user_list:
            user_path = self.players[user]["actions"][street_name]["pot_contribution"]
            user_pot_contribution = self._individual_pot_contribution(user_path)
            users_stake += user_pot_contribution     
        
        return users_stake
            
    def _side_pots(self, street_name, ratio = False):  # 사이드팟 생성함수
        
        # 해당 스트릿의 모든 유저
        all_user : list = list(self.actioned_queue) + self.all_in_users + self.fold_users

        # 해당 스트릿에서의 모든 유저의 팟 기여도
        users_pot_contribution = {
            position: self._individual_pot_contribution(self.players[position]["actions"][street_name]["pot_contribution"])
            for position in all_user
        }
        self.side_pots[street_name]['users_pot_contributions'] = users_pot_contribution

        # 해당 스트릿에서의 모든 유저의 팟 기여도 총합
        contribution_total = self._sum_individual_pot_contrbutions(street_name, all_user)
        self.side_pots[street_name]['contribution_total'] = contribution_total

        # 해당 스트릿까지의 팟 총액 기록
        self.side_pots[street_name]['pot_total'] = self.pot_total

        if ratio == True:
            for position in all_user:
                self.side_pots[street_name][position] = 0
                user_stake = 0
                user_contribution = users_pot_contribution[position]
                
                for _ , other_contribution in users_pot_contribution.items():
                    user_stake += min(other_contribution, user_contribution)
                
                self.side_pots[street_name]['stake_for_all'][position] = user_stake

        # 지분이 0이 아닌 포지션들만 추려서 오름차순으로 정렬
        contributors_ascending_order = deque(sorted(
            [position for position, contribution in users_pot_contribution.items() if contribution > 0],
            key=lambda position: users_pot_contribution[position]
        ))

        pots = {}  # 각 팟의 금액과 기여한 유저들을 저장할 딕셔너리
        pot_number = 0  # 사이드 팟 번호를 추적할 변수

        while contributors_ascending_order:
            # 가장 적은 지분을 가진 유저의 지분을 공통 지분으로 설정
            min_contribution = users_pot_contribution[contributors_ascending_order[0]]
            # 현재 포지션 리스트로 공통 지분을 모은 팟을 생성
            current_pot_total = min_contribution * len(contributors_ascending_order)

            contribution_total -= current_pot_total

            # 팟 이름 설정
            if pot_number == 0:
                pot_name = "main_pot"
            else:
                pot_name = f"side_pot_{pot_number}"

            # 팟 딕셔너리에 추가
            pots[pot_name] = {}
            pots[pot_name]['size'] = current_pot_total
            pots[pot_name]['contributors'] = list(contributors_ascending_order)
            
            contributers = contributors_ascending_order.copy()
            for position in contributers:
                users_pot_contribution[position] -= min_contribution
                if users_pot_contribution[position] == 0:
                    contributors_ascending_order.popleft()
                    users_pot_contribution.pop(position)

            pot_number += 1

        if contribution_total == 0:
            return pots
        else:
            raise ValueError("Sidepot calculation is incorrect.")
        
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
    
    def _compare_hand(self, user_cards : dict, community_cards : list):

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

        # live hands의 베스트 핸드를 랭크 순위대로 정렬하여 users_ranking 리스트 작성
        self.log_users_ranking = self._users_ranking()

        nuts = self.log_nuts

        return nuts

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
                    open_order.append(self.log_hand_cards[stage[0]][stage[1]])
                else:
                    open_order.append(self.log_hand_cards[stage])
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
    

    def _find_optimal_combination(self, winner_list, contributors):
        max_overlap = 0
        optimal_combination = []

        for subset_size in range(1, len(winner_list) + 1):  # 부분집합 크기를 1부터 시작
            for combo in combinations(winner_list, subset_size):
                overlap = len(set(combo) & set(contributors))
                if overlap > max_overlap:
                    max_overlap = overlap
                    optimal_combination = list(combo)
                elif overlap == max_overlap and len(combo) < len(optimal_combination):
                    optimal_combination = list(combo)

        return optimal_combination

    def _pot_award(self, nuts, street_name) -> None:
        winner_list = [winner for winner in nuts.keys()]
        
        for street in self.street_name:
            pots = self.side_pots[street].get('pots', {})
            for _ , pot in pots.items():
                pot_size = pot['size']
                contributors = pot['contributors']

                if len(winner_list) == 1:
                    winner = winner_list[0]
                    if winner in contributors:
                        self.players[winner]['stk_size'] += pot_size
                        self.pot_total -= pot_size
                    else:
                        share = pot_size // len(contributors)
                        for user in contributors:
                            self.players[user]['stk_size'] += share
                            self.pot_total -= share
                else:  
                    if any(winner in contributors for winner in winner_list):
                        winner_list = self._find_optimal_combination(winner_list, contributors)
                        quotient, remainder = divmod(pot_size, len(winner_list))
                        for winner in winner_list:
                            self.players[winner]['stk_size'] += quotient
                            self.pot_total -= quotient
                        if remainder:
                            for user in self._start_order(street_name):
                                if user in winner_list:
                                    self.players[user]['stk_size'] += remainder
                                    self.pot_total -= remainder
                                    break
                    else:
                        share = pot_size // len(contributors)
                        for user in contributors:
                            self.players[user]['stk_size'] += share
                            self.pot_total -= share

        if not self.pot_total == 0:
            print(self.pot_total)
        assert self.pot_total == 0



    # def _pot_award(self, street_name : str, nuts : dict, users_ranking : deque) -> None:
    #     '''
    #     (1) 맨 마지막까지 진행된 스트릿에서만 승자가 나온 경우 
    #         1. 승자가 한 명일 때
    #             ㄱ.short all in 으로 이긴 경우
    #                 $ winner 의 지분을 분배한 후
    #                 전체팟을 업데이트 하고 
    #                 winner를 순위표에서 뺀 다음
    #                 팟 총액이 0이 될때까지 루프 실행  (이하 루프를 환급 함수로 만들고 (2)에서 재사용할 수 있도록 리팩토링)
    #                     A. 남은 유저 랭킹에서 해당 등수 유저가 여러 명인 경우
    #                         해당 유저들의 해당 스트릿 팟 기여도를 모두 더한 후
    #                             a. 기여도 총합이 남은 팟보다 작으면 루프 실행
    #                                 $ 같은 등수의 유저들에게 각자 자신의 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             b. 기여도 총합이 남은 팟보다 크면
    #                                 $ 남은 팟을 각 유저의 팟 기여도 비율 만큼 돌려주고
    #                                 $ 나머지가 생긴 경우 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 줌
    #                             환급이 끝난 유저들을 순위표에서 빼고 다시 루프로 돌아감
    #                     B. 남은 유저 랭킹에서 해당 등수가 유일한 경우의 유저인 경우
    #                         해당유저의 해당 스트릿에서의 팟 기여도를 계산한 후 
    #                             $ 기여도가 전체팟보다 크면, 해당 유저에게 남은 팟을 전부 다 돌려주고, 전체 팟은 0으로 업데이트
    #                             $ 기여도가 전체팟보다 작으면, 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             환급이 끝난 유저를 순위표에서 빼고 다시 루프로 돌아감
    #             ㄴ. 그냥 이겼거나 full all in으로 이긴 경우
    #                 $ 전체팟을 승자에게 모두 주고, 전체팟을 0으로 업데이트
                        
    #         2. 승자가 여러 명일 때
    #             ㄱ. short all in 으로 이긴 사람이 승자 구성에 포함된 경우
    #                 지분이 가장 작은 순서대로 오름차순 정렬한 다음 (나머지 분배하는 것까지 함수로 만들어 (2).2.ㄱ.A에서 재사용)
    #                     $ 해당 스트릿에서 무승부인 승자들이 공통으로 가져갈 몫을 먼저 분배 한 후 (아래 로직 틀렸음)
    #                         공통 몫 = (무승부인 승자들이 포함된 스트리트에서 승자들을 제외한 해당스트리트의 라이브 유저들의 _sum_individual_pot_contributions + 해당스트리트 폴드 유저들의 _sum_individual_pot_contributions + 승자 발생 스트릿 이전 스트릿까지의 팟 총액) // 무승부 인원 수
    #                     $ 나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준 다음
    #                     $ 남은 팟은 해당 스트릿에서의 각자 지분만큼 돌려주고 전체팟을 업데이트 한다                
    #             ㄴ. 그냥 이겼거나 full all in으로 이긴 사람으로만 승자가 구성된 경우 
    #                     $ 전체 팟을 등분하여 무승부인 승자들에게 분배한 후
    #                     나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준다.

    #     (2) 맨 마지막까지 진행된 스트릿 이전 스트릿에서 승자가 나온 경우
    #         1. 승자가 1명일 때
    #             ㄱ.이전 스트릿에서 short all in 으로 이기는 경우 밖에 없다.
    #                 $ winner 의 지분을 분배한 후

    #                 전체팟을 업데이트 하고 
    #                 winner를 순위표에서 뺀 다음
    #                 순위표에 남은 유저들 중 승자가 발생한 스트릿 이전 스트릿의 라이브 유저들은 모두 제외하고

    #                 팟 총액이 0이 될때까지 루프 실행  (이하 (1)에서 만든 환급함수 재사용)  
    #                     A. 남은 유저 랭킹에서 해당 등수 유저가 여러 명인 경우
    #                         각 유저들의 각 스트릿에서의 팟 기여도를 모두 더한 후
    #                             a. 기여도 총합이 남은 팟보다 작으면 루프 실행
    #                                 $ 같은 등수의 유저들에게 각자 자신의 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             b. 기여도 총합이 남은 팟보다 크면
    #                                 $ 남은 팟을 각 유저의 팟 기여도 비율 만큼 돌려주고
    #                                 $ 나머지가 생긴 경우 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 줌
    #                         환급이 끝난 유저들을 순위표에서 빼고 다시 루프로 돌아감
                        
    #                     B. 남은 유저 랭킹에서 해당 등수가 유일한 경우의 유저인 경우
    #                         해당유저의 해당 스트릿에서의 팟 기여도를 계산한 후 
    #                             $ 기여도가 전체팟보다 크면, 해당 유저에게 남은 팟을 전부 다 돌려주고, 전체 팟은 0으로 업데이트
    #                             $ 기여도가 전체팟보다 작으면, 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             환금이 끝난 유저를 순위표에서 빼고 다시 루프로 돌아감
                        
    #                     순위표가 빈 경우 (환급함수와 별도로 구현)
    #                         패자들 중 승자와 다른 스트릿에 있는 유저들이 있는 경우
    #                         같은 스트릿에 있는 유저들을 모은 후 루프 실행 
    #                             해당 유저들에 대해 자신이 액션 종료한 스트릿에서 폴드한 유저들의 individual_pot_contribution을 다 더한 후 
    #                             이를 등분하여 환급

    #         2. 승자가 여러 명일 때 
    #             ㄱ. 이전 스트릿에서 short all in 으로 이긴 사람이 승자 구성에 반드시 포함된다
    #                 A. 무승부 인원들이 같은 스트릿에 있는 경우 
    #                     지분이 가장 작은 순서대로 오름차순 정렬한 다음    
    #                         $ 해당 스트릿에서 무승부인 승자들이 공통으로 가져갈 몫을 먼저 분배 한 후
    #                         $ 나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준 다음 (여기까지는 (1) 2.ㄱ. 과 같음)   

    #                     전체팟을 업데이트 하고 
    #                     무승부 인원들을 순위표에서 뺀 다음
    #                     순위표에 남은 유저들 중 무승부 승자가 발생한 스트릿 이전 스트릿의 라이브 유저들은 모두 제외하고

    #                     팟 총액이 0이 될때까지 루프 실행  (이하 (1)에서 만든 환급함수 재사용)  
    #                         A. 남은 유저 랭킹에서 해당 등수 유저가 여러 명인 경우
    #                             각 유저들의 각 스트릿에서의 팟 기여도를 모두 더한 후
    #                                 a. 기여도 총합이 남은 팟보다 작으면 루프 실행
    #                                     $ 같은 등수의 유저들에게 각자 자신의 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                                 b. 기여도 총합이 남은 팟보다 크면
    #                                     $ 남은 팟을 각 유저의 팟 기여도 비율 만큼 돌려주고
    #                                     $ 나머지가 생긴 경우 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 줌
    #                             환급이 끝난 유저들을 순위표에서 빼고 다시 루프로 돌아감
                            
    #                         B. 남은 유저 랭킹에서 해당 등수가 유일한 경우의 유저인 경우
    #                             해당유저의 해당 스트릿에서의 팟 기여도를 계산한 후 
    #                                 $ 기여도가 전체팟보다 크면, 해당 유저에게 남은 팟을 전부 다 돌려주고, 전체 팟은 0으로 업데이트
    #                                 $ 기여도가 전체팟보다 작으면, 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                                 환금이 끝난 유저를 순위표에서 빼고 다시 루프로 돌아감
                            
    #                         순위표가 빈 경우 (환급함수와 별도로 구현)
    #                             패자들 중 승자와 다른 스트릿에 있는 유저들이 있는 경우
    #                             같은 스트릿에 있는 유저들을 모은 후 루프 실행 
    #                                 해당 유저들에 대해 자신이 액션 종료한 스트릿에서 폴드한 유저들의 individual_pot_contribution을 다 더한 후 
    #                                 이를 등분하여 환급

    #                 B. 무승부 인원들이 서로 다른 스트릿에 있는 경우

     
    #     '''
    #     winner_list = [winner for winner in nuts.keys()]
    #     final_street_live_hands = self.all_in_users + list(self.actioned_queue)
    #     #  (1) 맨 마지막까지 진행된 스트릿에서만 승자가 나온 경우 
    #     if all(winner in final_street_live_hands for winner in winner_list):
    #         # 승자가 한 명일 때 
    #         max_value = max(self.side_pots[street_name]['stake_for_all'][winner].values())
    #         if len(winner_list) == 1:
    #             winner = winner_list[0]
    #             # short all in 으로 이긴 경우
    #             if self.side_pots[street_name]['stake_for_all'][winner] != max_value:
    #                 # winner 의 지분을 분배한 후 전체팟을 업데이트 하고
    #                 self.players[winner]['stk_size'] = self.side_pots[street_name]['stake_for_all'][winner]
    #                 self.pot_total -= self.side_pots[street_name]['stake_for_all'][winner]
    #                 # winner를 순위표에서 뺀 다음
    #                 users_ranking.popleft()
    #                 # 팟 총액이 0이 될때까지 루프 실행
    #                 while self.pot_total > 0:
    #                     # 남은 유저 랭킹에서 해당 등수 유저가 여러 명인 경우
    #                     if isinstance(users_ranking[0], tuple):
    #                         # 해당 유저들의 해당 스트릿 팟 기여도를 모두 더한 후
    #                         total_contribution = self._sum_individual_pot_contrbutions(street_name, users_ranking[0])
    #                         # 기여도 총합이 남은 팟보다 작으면
    #                         if total_contribution < self.pot_total:
    #                             # 같은 등수의 유저들에게 각자 자신의 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             for user in users_ranking[0]:
    #                                 user_pot_contribution = self._individual_pot_contribution(self.players[user]['actions'][street_name]["pot_contribution"])
    #                                 self.players[user]['stk_size'] += user_pot_contribution
    #                                 self.pot_total -= user_pot_contribution
    #                         # 기여도 총합이 남은 팟보다 크면
    #                         else:
    #                             pot_total = self.pot_total
    #                             total_by_ratio = 0
    #                             # 남은 팟을 각 유저의 팟 기여도 비율 만큼 돌려주고
    #                             for user in users_ranking[0]:
    #                                 user_pot_contribution = self._individual_pot_contribution(self.players[user]['actions'][street_name]["pot_contribution"])
    #                                 user_pot_contribution_by_ratio = (user_pot_contribution * self.pot_total)  // total_contribution
    #                                 self.players[user]['stk_size'] += user_pot_contribution_by_ratio
    #                                 self.pot_total -= user_pot_contribution_by_ratio
    #                                 total_by_ratio += user_pot_contribution_by_ratio
    #                             remainder = pot_total - total_by_ratio
    #                             # 나머지가 생긴 경우 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준 다음
    #                             if remainder:
    #                                 start_order = self._start_order(street_name)
    #                                 for user in start_order:
    #                                     if user in self.fold_users_total or user == winner:
    #                                         continue
    #                                     elif user not in users_ranking[0]:
    #                                         continue
    #                                     else:
    #                                         self.players[user]['stk_size'] += remainder
    #                                         self.pot_total -= remainder
    #                                         break
    #                         # 같은 등수의 유저들을 순위표에서 빼고 다시 루프로 돌아감
    #                         users_ranking.popleft()       
    #                     # 남은 유저 랭킹에서 해당 등수가 유일한 경우의 유저인 경우
    #                     else:
    #                         # 해당유저의 해당 스트릿에서의 팟 기여도를 계산한 후              
    #                         user_pot_contribution = self._individual_pot_contribution(self.players[users_ranking[0]]['actions'][street_name]["pot_contribution"])
    #                         # 기여도가 전체팟보다 크면
    #                         if user_pot_contribution >= self.pot_total:
    #                             #  해당 유저에게 남은 팟을 전부 다 돌려주고, 전체 팟은 0으로 업데이트
    #                             self.players[users_ranking[0]]['stk_size'] += self.pot_total
    #                             self.pot_total = 0
    #                         # 기여도가 전체팟보다 작으면 
    #                         elif user_pot_contribution < self.pot_total:
    #                             # 기여도 만큼만 돌려주고, 전체팟을 해당 기여도를 뺀 값으로 업데이트
    #                             self.players[users_ranking[0]]['stk_size'] += user_pot_contribution
    #                             self.pot_total -= user_pot_contribution
    #                         # 환금이 끝난 유저를 순위표에서 빼고 다시 루프로 돌아감
    #                         users_ranking.popleft()
 
    #                 assert self.pot_total == 0           
    #             # 그냥 이겼거나 full all in으로 이긴 경우, 전체팟을 승자에게 모두 주고, 전체팟을 0으로 업데이트
    #             else:
    #                 self.players[winner]['stk_size'] = self.pot_total
    #                 self.pot_total -= self.pot_total
    #                 assert self.pot_total == 0  
    #         # 승자가 여러 명일 때
    #         elif len(winner_list) > 1:
    #             # short all in 으로 이긴 사람이 승자 구성에 포함된 경우
    #             if any(self.side_pots[street_name]['stake_for_all'][winner] != max_value for winner in winner_list):
    #                 # 지분이 가장 작은 순서대로 오름차순 정렬한 다음
    #                 tie_winner_list = sorted(winner_list, key=lambda winner: self.side_pots[street_name]['stake_for_all'].get(winner, float('inf')))
    #                 # 해당 스트릿에서 무승부인 승자들이 공통으로 가져갈 몫을 먼저 분배 한 후
    #                 losers_list = [user for user in self.live_hands if user not in winner_list]
    #                 common_share = self.side_pots[street_name]['common_share']   
    #                 common_share += self._sum_individual_pot_contrbutions(street_name, losers_list)
    #                 quotient, remainder = divmod(common_share, len(tie_winner_list))
    #                 for winner in tie_winner_list:
    #                     self.players[winner]['stk_size'] += quotient
    #                     self.pot_total -= quotient
    #                 # 나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준 다음
    #                 start_order = self._start_order(street_name)
    #                 for user in start_order:
    #                     if user in self.fold_users_total:
    #                         continue
    #                     elif user not in winner_list:
    #                         continue
    #                     else:
    #                         self.players[user]['stk_size'] += remainder
    #                         self.pot_total -= remainder
    #                         break
    #                 # 남은 팟은 해당 스트릿에서의 각자 지분만큼 돌려주고 전체팟을 업데이트 한다
    #                 for winner in tie_winner_list:
    #                     stake = self._individual_pot_contribution(self.players[winner]['actions'][street_name]["pot_contribution"])
    #                     self.players[winner]['stk_size'] += stake
    #                     self.pot_total -= stake
    #                 assert self.pot_total == 0

    #             # 그냥 이겼거나 full all in으로 이긴 사람으로만 승자가 구성된 경우
    #             else:
    #                 # 전체 팟을 등분하여 무승부인 승자들에게 분배한 후 
    #                 quotient, remainder = divmod(self.pot_total, len(winner_list))
    #                 for winner in winner_list:
    #                     self.players[winner]['stk_size'] = quotient
    #                     self.pot_total -= quotient
    #                 # 나머지는 버튼에서 왼쪽 방향으로 가장 가까운 사람에게 준다.
    #                 for user in self.start_order:
    #                     if user in self.fold_users_total:
    #                         continue
    #                     elif user not in winner_list:
    #                         continue
    #                     else:
    #                         self.players[user]['stk_size'] += remainder
    #                         self.pot_total -= remainder
    #                         break
        
    #                 assert self.pot_total == 0            

       

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    AUXILIARY                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
    def _posting_blind(self, street_name):
        if self.stakes == "low":
            self.players["SB"]["stk_size"] -= self.SB
            self.players["BB"]["stk_size"] -= self.BB
            self.players["SB"]["actions"][street_name]["betting_size_total"]["bet"].append(self.SB)
            self.players["SB"]["actions"][street_name]["action_list"].append("bet")
            self.players["BB"]["actions"][street_name]["betting_size_total"]["bet"].append(self.BB)
            self.players["BB"]["actions"][street_name]["action_list"].append("bet")
            self.pot_total += (self.SB + self.BB)

    def _check_connection(self, on_user_list):
        connected_users = []
        if on_user_list:
            for on_user in on_user_list:
                connected_users.append(self.user2pos[on_user])
            for position in self.start_order:
                if position not in connected_users:
                    self.fold_users_total[position] = self.start_order.popleft()

    def _initialize_start_order(self, street_name):
        if street_name == 'pre_flop':
            if self.rings == 6:
                self.start_order = deque(["UTG", "HJ", "CO", "D", "SB", "BB"])
            elif self.rings == 9:
                self.start_order = deque(['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB'])
        else:
            if self.rings == 6:
                self.start_order = deque(["SB", "BB", "UTG", "HJ", "CO", "D"])
            elif self.rings == 9:
                self.start_order = deque(['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D'])
            new_order = []
            while self.start_order:
                position = self.start_order.popleft()
                if position in self.survivors:
                    new_order.append(position)
            self.start_order = deque(new_order)

    def _start_order(self, street_name):
        if street_name == 'pre_flop':
            if self.rings == 6:
                start_order =["UTG", "HJ", "CO", "D", "SB", "BB"]             
            elif self.rings == 6:
                start_order = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']
        else:
            if self.rings == 6:
                start_order = ["SB", "BB", "UTG", "HJ", "CO", "D"]            
            elif self.rings == 9:
                start_order = ['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D']     

        return start_order



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
    
    def _prep_preFlop(self, street_name):
        
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

    def _prep_street(self, street_name):
        
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
            # answer = self.test_code_action_info(current_player, possible_actions, street_name)
            answer = self.get_input()

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

    def _finishing_street(self, street_name):

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
        # self.test_code_street_info(street_name)

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                      HAND                                                                        #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def _preFlop(self, stk_size):
        
        street_name = "pre_flop"
        self._prep_preFlop(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            # self.test_code_showdown_info()

            self._pot_award(nuts, street_name)
            
            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._flop(stk_size)
    
    def _flop(self, stk_size):
    
        street_name = "flop"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            # self.test_code_showdown_info()

            self._pot_award(nuts, street_name)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._turn(stk_size)
    
    def _turn(self, stk_size):

        street_name = "turn"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            # self.test_code_showdown_info()

            self._pot_award(nuts, street_name)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            self._river(stk_size)
    
    def _river(self, stk_size):

        street_name = "river"
        self._prep_street(street_name)
        self._play_street(street_name)
        self._finishing_street(street_name)
        showdown = self._end_conditions(street_name)
        if showdown:
            nuts = self._showdown(street_name)
             # 테스트 코드
            # self.test_code_showdown_info()

            self._pot_award(nuts, street_name)

            # 테스트 코드
            self.test_code_pot_award_info(stk_size)
        else:
            raise SystemExit("!!!!!!!!!!!!!!종료조건에 걸리지 않는 상황입니다. 유저들의 액션을 검토해서 종료조건을 수정하거나 추가하세요!!!!!!!!!!!!!!")

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    EXECUTION                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def go_street(self, stk_size):
        self._preFlop(stk_size)     

    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                                    TEST CODE                                                                     #
    ####################################################################################################################################################
    ####################################################################################################################################################

    def get_input(self):
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
        print("=====================쇼다운 결과=====================")
        print(f'best hands : {self.log_best_hands}')
        print(f'users_ranking : {self.log_users_ranking}')
        print(f'nuts : {self.log_nuts}')
        print()

    def test_code_pot_award_info(self, stk_size):
        # if len(self.log_nuts) == 3 or len(self.log_nuts) == 4 or len(self.log_nuts) == 5:
        if len(self.log_nuts) == 2:
            print("=====================쇼다운 결과=====================")
            print(f'best hands : {self.log_best_hands}')
            print(f'users_ranking : {self.log_users_ranking}')
            print(f'nuts : {self.log_nuts}')
            print()
            print("====================팟 분배 결과====================")
            print(f'side_pots 생성 결과 : {self.side_pots}')
            print()
            for id, position in zip(stk_size, self.players):
                stack_size = self.players[position]['stk_size']
                print(f'{position} 의 stk_size 변화 : {stk_size[id]} -> {stack_size}')








