import random
from itertools import combinations
from collections import OrderedDict, defaultdict, Counter, deque

class Base:
    
    def __init__(self, user_id_list, stk_size, rings, stakes):

        self.user_id_list = user_id_list
        self.stk_size = stk_size
        self.rings = rings
        self.stakes = stakes
  
        self.SB, self.BB = self._blind_post()

        self.log_hand_actions = {"pre_flop" : [], "flop" : [], "turn" : [], "river" : []}        
        self.log_hand_cards = {"burned" : [], "flop" : [], "turn" : [], "river" : [], "table_cards" : []} 
        
        self.log_best_hands = OrderedDict() # 쇼다운하여 모든 live_hands 의 best_hands의 랭크 이름과 해당 카드 조합 및 키커를 포지션별로 모은 딕셔너리
        self.log_nuts = {} # best_hands 중 가장 강력한 핸드를 담은 딕셔너리
        self.log_users_ranking = None # 유저 랭킹 리스트
        

        self.positions_6 = ["UTG", "HJ", "CO", "D", "SB", "BB"]
        self.positions_9 = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']

        # user_id to position 딕셔너리 생성
        self.user2pos = self._assign_user2pos(user_id_list)

        # 덱 생성 및 셔플
        self.shuffled_deck = self._shuffle_deck()

        # 플레이어 초기화 및 카드 딜링
        self.players, self.stub = self._initialize_players(user_id_list, stk_size, self.shuffled_deck)

        self.hand_power = {
            "royal_straight_flush": 10,
            "straight_flush": 9,
            "quads": 8,
            "full_house": 7,
            "flush": 6,
            "straight": 5,
            "set": 4,
            "trips": 4,
            "two_pair": 3,
            "one_pair": 2,
            "high_card": 1
        }

        self.card_rank_order = "23456789TJQKA"

    def _blind_post(self):
        if self.stakes == "low":
            sb = 1
            bb = 2
        elif self.stakes == "high":
            sb = 2
            bb = 5
        return sb, bb

    def _get_positions(self, rings):
        if rings == 6:
            return self.positions_6
        elif rings == 9:
            return self.positions_9
        else:
            raise ValueError("Invalid number of rings. Must be 6 or 9.")

    def _shuffle_positions(self, positions): 
        shuffled_positions = random.sample(positions, len(positions))
        return shuffled_positions

    def _assign_user2pos(self, user_id_list):
        positions = self._shuffle_positions(self._get_positions(self.rings)) 
        user2pos = {user_id: position for position, user_id in zip(positions, user_id_list)}
        return user2pos

    def _shuffle_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']  # H: 하트, D: 다이아몬드, C: 클로버, S: 스페이드
        deck = [rank + suit for suit in suits for rank in ranks]
        shuffled_deck = random.sample(deck, len(deck))
        return shuffled_deck
    
    def _dealing_cards(self, players, shuffled_deck):
        for _ in range(2):
            for position in players:
                players[position]['starting_cards'].append(shuffled_deck.pop(0))

        return players, shuffled_deck

    def _initialize_players(self, user_id_list, stk_size, shuffled_deck):
        positions = self._get_positions(self.rings) # 테스트 코드
        # positions = self._shuffle_positions(self._get_positions(self.rings)) # 실제코드
        players = {position: {
            "user_id": user_id,
            "stk_size": stk_size[user_id],
            "starting_cards": [],
            "actions": {
                street: {"action_list": [], 
                        "pot_contribution": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]},
                        "betting_size_total": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]},
                        }
                for street in ["pre_flop", "flop", "turn", "river"]
            }
        } for position, user_id in zip(positions, user_id_list)}
        
        players, stub = self._dealing_cards(players, shuffled_deck)
        return players, stub

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
    #                                                                AUXILIARY SHOWDOWN                                                                #
    ####################################################################################################################################################
    ####################################################################################################################################################
   
    def _card_rank(self, card):
            return self.card_rank_order.index(card[0])

    def _flush(self, cards):
            suits = [card[1] for card in cards]
            return len(set(suits)) == 1

    def _straight(self, cards):
        ranks = sorted(set(self._card_rank(card) for card in cards), reverse=True)
        for i in range(len(ranks) - 4):
            if ranks[i] - ranks[i + 4] == 4:
                return True
        return False
    
    def _classify_hand(self, cards, pocket_cards):
        cards = sorted(cards, key=self._card_rank, reverse=True)
        ranks = [card[0] for card in cards]
        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)

        made_flush = self._flush(cards)
        made_straight = self._straight(cards)

        if made_flush and made_straight:
            if ranks[:5] == ['A', 'K', 'Q', 'J', 'T']:
                return "royal_straight_flush", cards[:5]
            return "straight_flush", cards[:5]
        
        if counts == [4, 1]:
            quads_rank = next(rank for rank, count in rank_counts.items() if count == 4)
            quads = [card for card in cards if card[0] == quads_rank]
            return "quads", quads

        if counts == [3, 2]:
            three_of_a_kind_rank = next(rank for rank, count in rank_counts.items() if count == 3)
            pair_rank = next(rank for rank, count in rank_counts.items() if count == 2)
            three_of_a_kind = [card for card in cards if card[0] == three_of_a_kind_rank]
            pair_cards = [card for card in cards if card[0] == pair_rank]
            return "full_house", three_of_a_kind + pair_cards[:2]

        if made_flush:
            return "flush", cards[:5]

        if made_straight:
            straight = sorted(set(cards), key=self._card_rank, reverse=True)
            for i in range(len(straight) - 4):
                if self._card_rank(straight[i]) - self._card_rank(straight[i + 4]) == 4:
                    return "straight", straight[i:i + 5]

        if counts == [3, 1, 1]:
            three_of_a_kind_rank = next(rank for rank, count in rank_counts.items() if count == 3)
            three_of_a_kind = [card for card in cards if card[0] == three_of_a_kind_rank]
            if all(card in pocket_cards for card in three_of_a_kind[:2]):
                return "set", three_of_a_kind
            return "trips", three_of_a_kind

        if counts == [2, 2, 1]:
            pair_rank = sorted((rank for rank, count in rank_counts.items() if count == 2), key=self.card_rank_order.index, reverse=True)
            two_pair = [card for card in cards if card[0] in pair_rank]
            return "two_pair", two_pair

        if counts == [2, 1, 1, 1]:
            pair_rank = next(rank for rank, count in rank_counts.items() if count == 2)
            one_pair = [card for card in cards if card[0] == pair_rank]
            return "one_pair", one_pair

        return "high_card", cards[:5]
    
    def _make_best_hands(self, pocket_cards, community_cards):
        best_rank_name = None
        best_hand = None
        best_rank_value = 0
        best_hands_dict = defaultdict(list)
        live_hands = pocket_cards + community_cards

        for combo in combinations(live_hands, 5):
            rank_name, hand = self._classify_hand(list(combo), pocket_cards)
            rank_value = self.hand_power[rank_name]
            if rank_value > best_rank_value:
                best_rank_name = rank_name
                best_rank_value = rank_value
                best_hands_dict[rank_name] = [hand]
            elif rank_value == best_rank_value:
                best_hands_dict[rank_name].append(hand)

        # 가장 높은 핸드 조합 선택
        best_hand = max(best_hands_dict[best_rank_name], key=lambda hand: [self._card_rank(card) for card in hand])
        remaining_cards = [card for card in live_hands if card not in best_hand]
        best_kicker = sorted(remaining_cards, key=self._card_rank, reverse=True)

        kicker_mapping = {
            "one_pair": 3,
            "two_pair": 1,
            "trips": 2,
            "quads": 1 if all(card in community_cards for card in best_hand) else 0
        }

        best_kicker = best_kicker[:kicker_mapping.get(best_rank_name, 0)]

        return {best_rank_name: best_hand, "kicker": best_kicker}

    def _resolve_ties(self, nuts_positions):
        if len(nuts_positions) <= 1:
            return nuts_positions

        best_hands = [self.log_best_hands[pos] for pos in nuts_positions]

        # 랭크별 비교할 카드 수 설정
        rank_card_count = {
            "one_pair": 2,
            "two_pair": 4,
            "trips": 3,
            "set": 3,
            "quads": 4,
            "full_house": 5,
            "flush": 5,
            "straight": 5,
            "straight_flush": 5,
            "royal_straight_flush": 5,
            "high_card": 5
        }

        best_rank_name = next(iter(best_hands[0]))
        compare_count = rank_card_count[best_rank_name]

        # 핸드 비교
        for i in range(compare_count):
            max_rank = max(self._card_rank(hand[best_rank_name][i]) for hand in best_hands)
            best_hands = [hand for hand in best_hands if self._card_rank(hand[best_rank_name][i]) == max_rank]
            if len(best_hands) == 1:
                break
        else:
            self.tie_flag = True  # 핸드 비교 후에도 무승부일 때 플래그 설정

        # 핸드가 모두 동일한 경우 키커 비교
        if len(best_hands) > 1 and any(hand['kicker'] for hand in best_hands):
            max_kicker_length = max(len(hand['kicker']) for hand in best_hands)
            for i in range(max_kicker_length):
                max_kicker_rank = max(self._card_rank(hand['kicker'][i]) for hand in best_hands if len(hand['kicker']) > i)
                best_hands = [hand for hand in best_hands if len(hand['kicker']) > i and self._card_rank(hand['kicker'][i]) == max_kicker_rank]
                if len(best_hands) == 1:
                    break
            else:
                self.tie_flag = True  # 키커 비교 후에도 무승부일 때 플래그 설정

        # 최종 넛츠 포지션 반환
        final_nuts_positions = [pos for pos in nuts_positions if self.log_best_hands[pos] in best_hands]

        return final_nuts_positions

    def _hand_key(self, position):
        hand_name = next(iter(self.log_best_hands[position]))
        hand_combinations = self.log_best_hands[position][hand_name]
        card_ranks = [self._card_rank(card) for card in hand_combinations]
        kicker_ranks = [self._card_rank(card) for card in self.log_best_hands[position].get('kicker', [])]
        return (self.hand_power[hand_name], card_ranks, kicker_ranks)

    def _users_ranking(self) -> list:
        '''
        쇼다운 결과 커뮤니티 카드 5장과 유저의 스타팅 카드 2장으로 만들수 있는
        베스트 핸드들의 딕셔너리 self.log_best_hands를 받아서
        핸드 랭크 이름으로 먼저 비교하고, 
        이름이 같으면 핸드를 이루는 카드 조합의 카드 랭크를 앞에서부터 순서대로 비교하고, 
        카드 랭크도 같으면 키커가 있는 경우 키커까지 비교해서
        핸드의 파워가 강력한 순서로 해당 핸드를 가진 유저의 포지션을 내림차순 정렬하고,
        키커까지 모두 똑같아서 무승부인 유저들은 튜플로 묶은 리스트를 반환하는 함수
        '''
        positions = list(self.log_best_hands.keys())
        users_ranking_list = sorted(positions, key=lambda position: self._hand_key(position), reverse=True)
        
        tied_players = []
        ranked_users = []

        previous_key = None
        current_tie_group = []

        for pos in users_ranking_list:
            current_key = self._hand_key(pos)

            if previous_key is not None and current_key == previous_key:
                current_tie_group.append(pos)
            else:
                if current_tie_group:
                    tied_players.append(tuple(current_tie_group))
                    current_tie_group = []
                current_tie_group.append(pos)

            previous_key = current_key

        if current_tie_group:
            tied_players.append(tuple(current_tie_group))

        for group in tied_players:
            if len(group) == 1:
                ranked_users.append(group[0])
            else:
                ranked_users.append(group)

        self.log_users_ranking = ranked_users
        users_ranking = deque(ranked_users).copy()

        return users_ranking
    
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
    
    ####################################################################################################################################################
    ####################################################################################################################################################
    #                                                               AUXILIARY POT AWARD                                                                #
    ####################################################################################################################################################
    ####################################################################################################################################################
    
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
