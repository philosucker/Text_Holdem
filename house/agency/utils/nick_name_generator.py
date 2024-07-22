import random
import string

def generate_random_nickname() -> str:
    return ''.join(random.choices(string.ascii_letters, k=8))

