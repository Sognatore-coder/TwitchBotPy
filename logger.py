# Создаёт {ID}.log для каждого пользователя
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def log(user_id: int, action: str, result: str = ""):
    path = os.path.join(LOG_DIR, f"{user_id}.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ACTION: {action}\n")
        if result:
            f.write(f"[{timestamp}] RESULT: {result}\n")
        f.write("\n")
