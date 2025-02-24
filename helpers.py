import random
import string
import time
from database import get_user, update_user

def generate_short_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def can_generate_link(user_id):
    user = get_user(user_id)
    if user["count"] >= 5:
        if time.time() - user["last_time"] < 600:
            return False, 600 - (time.time() - user["last_time"])
        update_user(user_id, {"count": 0, "last_time": time.time()})
    return True, None

def increment_user_count(user_id):
    update_user(user_id, {"$inc": {"count": 1}, "$set": {"last_time": time.time()}})
