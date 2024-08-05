from beanie import Document
from pydantic import BaseModel, Field
from collections import deque

class Connection(BaseModel):
    connected: bool = False
    entry_time: str = None
    exit_time: str = None

class UserLog(Document):
    user_email : str = None 
    user_nick : str = None
    connection_log : Connection

    class Settings:
        collection = "user_log"  # MongoDB 컬렉션 이름

class TableLog(Document):
    table_id: str = None
    creation_time: str = None
    dismissed_time : str = None
    rings: int = 0
    stakes: str = None
    agent: dict[str, int] = Field(default_factory=dict) # {"hard" : 2, "easy" : 1}
    now: int = 0
    max: int = rings
    status: str = None # waiting, playing, dismissed
    new_players: dict[str, int] = Field(default_factory=dict) # {"nick_4" : 0, "nick_5": 0, "nick_6" : 0}
    continuing_players: dict[str, int] = Field(default_factory=dict) # {"nick_1" : 100, "nick_2": 2000, "nick_3" : 500}
    determined_positions: dict[str, str] = Field(default_factory=dict) # {"nick_1" : "BB", "nick_2": "CO", "nick_3" : D}

    class Settings:
        collection = "table_log"

class ActionDetails(BaseModel):
    action_list: list[str] = Field(default_factory=list)
    pot_contribution: dict[str, list[int]] = Field(default_factory=lambda: {"call": [0], "raise": [0], "all-in": [0], "bet": [0]})
    betting_size_total: dict[str, list[int]] = Field(default_factory=lambda: {"call": [0], "raise": [0], "all-in": [0], "bet": [0]})

class PlayerActions(BaseModel):
    pre_flop: ActionDetails = Field(default_factory=ActionDetails)
    flop: ActionDetails = Field(default_factory=ActionDetails)
    turn: ActionDetails = Field(default_factory=ActionDetails)
    river: ActionDetails = Field(default_factory=ActionDetails)

class Player(BaseModel):
    user_nick: str
    stk_size: int
    starting_cards: list[str] = Field(default_factory=list)
    actions: PlayerActions = Field(default_factory=PlayerActions)

class LogPlayers(BaseModel):
    players: dict[str, Player] = Field(default_factory=dict)

class PotDetails(BaseModel):
    size: int
    contributors: list[str] = Field(default_factory=list)

class StreetDetails(BaseModel):
    users_pot_contributions: dict[str, int] = Field(default_factory=dict)
    contribution_total: int
    pot_total: int
    stake_for_all: dict[str, int] = Field(default_factory=dict)
    pots: dict[str, PotDetails] = Field(default_factory=dict)

class LogSidePots(BaseModel):
    pre_flop: StreetDetails
    flop: StreetDetails
    turn: StreetDetails
    river: StreetDetails

class LogHandActions(BaseModel):
    pre_flop: list[str] = Field(default_factory=list)
    flop: list[str] = Field(default_factory=list)
    turn: list[str] = Field(default_factory=list)
    river: list[str] = Field(default_factory=list)

class LogCommunityCards(BaseModel):
    burned: list[str] = Field(default_factory=list)
    flop: list[str] = Field(default_factory=list)
    turn: list[str] = Field(default_factory=list)
    river: list[str] = Field(default_factory=list)
    table_cards: list[str] = Field(default_factory=list)

class HandDetails(BaseModel):
    hand: list[str] = Field(default_factory=list)
    kicker: list[str] | None = Field(default_factory=list)

class LogBestHands(BaseModel):
    best_hands: dict[str, HandDetails] = Field(default_factory=dict)

class LogNuts(BaseModel):
    nuts: dict[str, HandDetails] = Field(default_factory=dict)

class LogUsersRanking(BaseModel):
    users_ranking: deque[str | tuple[str, ...]] = Field(default_factory=deque)

class GameLog(Document):
    start_time: str = None
    end_time: str = None
    players: LogPlayers
    side_pots: LogSidePots
    pot_change: list = None 
    hand_actions: LogHandActions
    community_cards: LogCommunityCards
    best_hands: LogBestHands
    nuts: LogNuts
    users_ranking: LogUsersRanking

    class Settings:
        collection = "game_log"

class ChatLog(Document):
    chat_id : str = None
    user_nick: str = None 
    content: str = None
    timestamp: str = None

    class Settings:
        collection = "chat_log"