
import secrets
import string

async def generate_unique_code(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def replace_ru_to_en(text: str):
    text = text.lower()
    letters = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "u",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
    new_text = ""
    for letter in text:
        if letter in letters:
            new_text += letters[letter]
        else:
            new_text += letter
    return new_text

async def get_referal_link(code: str, group_name: str):
    en_group_name = await replace_ru_to_en(group_name)
    # return f"https://t.me/homew0rk_testing_bot?start=invite_{code}_{en_group_name}"
    return f"https://t.me/homew0rk_bot?start=invite_{code}_{en_group_name}"  