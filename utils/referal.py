
import secrets
import string

async def generate_unique_code(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def get_referal_link(code: str):
    # return f"https://t.me/homew0rk_bot?start=ref_{code}"  
    return f"https://t.me/homew0rk_testing_bot?start=ref_{code}"