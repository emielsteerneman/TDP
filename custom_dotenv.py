import os

def load_dotenv(filepath=".env"):
    if not os.path.exists(filepath): return

    lines = open(filepath, 'r').readlines()
    for line in lines:
        if not line.startswith("#"):
            equals_index = line.find("=")
            if equals_index == -1: continue
            key, value = line[:equals_index], line[equals_index+1:]
            value = value.strip()
            if value.startswith('"') and value.endswith('"'): value = value[1:-1]
            os.environ[key] = value