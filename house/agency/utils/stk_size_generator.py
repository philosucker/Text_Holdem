import random

def generate_random_stk_size(difficulty: str) -> int:
    if difficulty == "easy":
        return random.randint(100, 500)
    elif difficulty == "hard":
        return random.randint(5000, 10000)
    return 0
