# log.py
import logging
import os
import datetime

def setup_logger():
  """
  Настраивает логгер, который пишет в файл и выводит сообщения в консоль.
  """
  # Убедимся, что папка для логов существует
  log_dir = "data/logs"
  os.makedirs(log_dir, exist_ok=True)

  # Создаём имя файла для логов на основе текущей даты
  log_filename = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")

  # Создаём главный логгер
  logger = logging.getLogger("DomashkaBot")
  logger.setLevel(logging.INFO)

  # Проверяем, чтобы обработчики не дублировались
  if not logger.hasHandlers():
    # Настраиваем обработчик для записи в файл
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
      datefmt="%d.%m.%Y %H:%M:%S"
    ))

    # Настраиваем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
      "[%(levelname)s] %(message)s"
    ))

    # Добавляем обработчики в логгер
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

  return logger


# Получение настроенного логгера
logger = setup_logger()
