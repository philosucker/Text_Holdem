import secrets

def generate_secret_key(length: int = 32) -> str:
    return secrets.token_hex(length)

def save_secret_key_to_env(env_file: str = './house/.env', key_name: str = 'SECRET_KEY'):
    secret_key = generate_secret_key()
    with open(env_file, 'r') as file:
        lines = file.readlines()
    
    with open(env_file, 'w') as file:
        for line in lines:
            if line.startswith(f"{key_name}="):
                file.write(f"{key_name}={secret_key}\n")
            else:
                file.write(line)
        if not any(line.startswith(f"{key_name}=") for line in lines):
            file.write(f"{key_name}={secret_key}\n")
