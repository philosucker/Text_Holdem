import random

class PreInitializer:
    
    def __init__(self, user_id_list, stk_size, rings, stakes):
        self.positions_6 = ["UTG", "HJ", "CO", "D", "SB", "BB"]
        self.positions_9 = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'D', 'SB', 'BB']

        self.rings = rings
        self.stakes = stakes

        self.SB, self.BB = self._blind_post(stakes)
        self.main_pot = 0
        self.side_pot = None

        self.hand_actions = {"pre_flop" : [], "flop" : [], "turn" : [], "river" : []}
        

        # 포지션과 유저 ID를 할당
        self.players, self.user2pos = self._assign_user2pos(user_id_list)

        # 덱 생성 및 셔플
        deck = self._create_deck()
        self.shuffled_deck = self._shuffle_deck(deck)

        # 플레이어 초기화 및 카드 딜링
        self.players, self.stub = self._initialize_players(user_id_list, stk_size, self.players, self.shuffled_deck, self.stakes)
        
        

    def _position_num(self, rings):
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
        positions = self._shuffle_positions(self._position_num(self.rings)) 
        players = {position: {"user_id": user_id} for position, user_id in zip(positions, user_id_list)}
        user2pos = {user_id: position for position, user_id in zip(positions, user_id_list)}
        return players, user2pos

    def _create_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['H', 'D', 'C', 'S']  # H: 하트, D: 다이아몬드, C: 클로버, S: 스페이드
        deck = [rank + suit for suit in suits for rank in ranks]
        return deck

    def _shuffle_deck(self, deck):
        shuffled_deck = random.sample(deck, len(deck))
        return shuffled_deck
    
    def _dealing_cards(self, players, shuffled_deck):
        for _ in range(2):
            for position in players:
                players[position]['starting_cards'].append(shuffled_deck.pop(0))
        
        return players, shuffled_deck
    
    def _blind_post(self, stakes):
        if stakes == "low":
            sb = 1
            bb = 2
        elif stakes == "high":
            sb = 2
            bb = 5
        return sb, bb


    def _initialize_players(self, user_id_list, stk_size, players, shuffled_deck, stakes):
        # 각 user_id에 해당하는 stk_size 값을 players 딕셔너리에 추가합니다.
        for position, info in players.items():
            user_id = info['user_id']
            if user_id in user_id_list:
                players[position]['stk_size'] = stk_size[user_id]
                players[position]['starting_cards'] = []  
                players[position]['actions'] = {
                    "pre_flop": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                    "flop": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                    "turn": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                    "river": {"action_list" : [], "betting_size": {"call": [0], "raise": [0], "all-in": [0], "bet": [0]}},
                }

            else:
                pass  # 예외처리
        
        players, stub = self._dealing_cards(players, shuffled_deck)

        return players, stub