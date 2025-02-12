from variables import postfixes

def process_subject_name(subject: str, subjects_map: dict, prefixes_map: dict = None) -> str:

    """
    Обрабатывает название предмета, заменяя префиксы и длинные названия.

    Args:
        subject (str): Название предмета из расписания.
        subjects_map (dict): Словарь с заменами названий предметов.
        prefixes_map (dict, optional): Словарь с заменами префиксов.

    Returns:
        str: Обработанное название.
    """
    if subject == "-":
        return subject
    
    if subject.startswith("Лаб.Информатика"):
        subject = subject.replace("Лаб.Информатика", "Информатика")
        
    prefix: str = None
    subject_name: str = subject
    postfix: str = None

    for pr, _ in prefixes_map.items():
        if pr in subject.lower():
            prefix = subject_name[:len(pr)]
            break

    for pf in postfixes:
        if pf in subject:
            postfix = pf
            break
        else:
            postfix = ""

    if prefix:
        subject_name = subject_name.replace(prefix, "")

    if postfix:
        subject_name = subject_name.replace(postfix, "")

    processed_prefix: str = prefixes_map.get(prefix.lower(), prefix) if (prefixes_map is not None and prefix is not None) else ""
    processed_subject_name: str = subjects_map.get(subject_name.lower(), subject_name) if (subjects_map is not None) else ""

    if processed_prefix is not None:
        if processed_prefix.endswith("."):
            processed_prefix += " "

    processed_prefix = "" if prefix is None else processed_prefix
    postfix = "" if postfix is None else postfix

    processed_subject = f"{processed_prefix}{processed_subject_name}{postfix}"

    return processed_subject