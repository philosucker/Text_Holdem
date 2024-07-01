import random
from itertools import combinations
from collections import OrderedDict, defaultdict, Counter

class Base:
    
    def __init__(self, user_id_list, stk_size, rings, stakes):

        self.positions_6 = ["UTG", "HJ", "CO", "D", "SB", "BB"]
        self.positions_9 = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']

        # self.user_id_list = user_id_list
        # self.stk_size = stk_size
        self.rings = rings
        self.stakes = stakes
  
        self.SB, self.BB = self._blind_post()

        self.log_hand_actions = {"pre_flop" : [], "flop" : [], "turn" : [], "river" : []}
        self.log_hand_main_pots =  {"pre_flop" : None, "flop" : None, "turn" : None, "river" : None}
        self.log_hand_cards = {"burned" : [], "flop" : [], "turn" : [], "river" : [], "table_cards" : []} 
        
        self.log_best_hands = OrderedDict() # live_hands 의 best_hands를 모은 딕셔너리
        self.log_nuts = {} # best_hands 중 가장 강력한 핸드를 담은 딕셔너리
        self.log_users_ranking = None # 유저 랭킹 리스트

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
        positions = self._shuffle_positions(self._get_positions(self.rings)) 
        players = {position: {"user_id": user_id} for position, user_id in zip(positions, user_id_list)}
        # 각 user_id에 해당하는 stk_size 값을 players 딕셔너리에 추가합니다.
        for position, info in players.items():
            user_id = info['user_id']
            players[position]['stk_size'] = stk_size[user_id]
            players[position]['starting_cards'] = []

            # "betting_size" 에 적히는 값들은 항상 total을 의미
            players[position]['actions'] = {
                "pre_flop": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                "flop": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                "turn": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                "river": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
            }
        
        players, stub = self._dealing_cards(players, shuffled_deck)

        return players, stub
    
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
    
    def classify_hand(self, cards, pocket_cards):
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
            rank_name, hand = self.classify_hand(list(combo), pocket_cards)
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

        # 핸드가 모두 동일한 경우 키커 비교
        if len(best_hands) > 1 and any(hand['kicker'] for hand in best_hands):
            max_kicker_length = max(len(hand['kicker']) for hand in best_hands)
            for i in range(max_kicker_length):
                max_kicker_rank = max(self._card_rank(hand['kicker'][i]) for hand in best_hands if len(hand['kicker']) > i)
                best_hands = [hand for hand in best_hands if len(hand['kicker']) > i and self._card_rank(hand['kicker'][i]) == max_kicker_rank]
                if len(best_hands) == 1:
                    break

        # 최종 넛츠 포지션 반환
        final_nuts_positions = [pos for pos in nuts_positions if self.log_best_hands[pos] in best_hands]
        return final_nuts_positions

    def _users_ranking(self):
        positions = list(self.log_best_hands.keys())
        self.log_users_ranking = sorted(positions, key=lambda pos: (
            self.hand_power[next(iter(self.log_best_hands[pos]))],
            [self._card_rank(card) for card in self.log_best_hands[pos][next(iter(self.log_best_hands[pos]))]],
            [self._card_rank(card) for card in self.log_best_hands[pos]['kicker']]
        ), reverse=True)

