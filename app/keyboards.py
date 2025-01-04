from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

start_keyboard_admin = ReplyKeyboardMarkup(keyboard=[
  [KeyboardButton(text="👀 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
  [KeyboardButton(text="❌ Удалить Д/З"), KeyboardButton(text="Админ-панель 😈")],
  [KeyboardButton(text="🔄 Сбросить дедлайн Д/З 🔄")]
  ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

start_keyboard_adder = ReplyKeyboardMarkup(keyboard=[
  [KeyboardButton(text="👀 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

start_keyboard = ReplyKeyboardMarkup(keyboard=[
  [KeyboardButton(text="👀 Посмотреть Д/З")]
], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

async def get_start_keyboard(role):
  global start_keyboard
  global start_keyboard_adder

  if role == 2:
    return start_keyboard_adder
  elif role >= 3:
    return start_keyboard_admin
  else:
    return start_keyboard

see_hw_keyboard = ReplyKeyboardMarkup(keyboard=[
  [KeyboardButton(text="Посмотреть по предмету")],
  [KeyboardButton(text="На сегодня"), KeyboardButton(text="На завтра"), KeyboardButton(text="На послезавтра")],
  [KeyboardButton(text="🗓 По дате"), KeyboardButton(text="Назад ↩️")],
], resize_keyboard=True, input_field_placeholder="Выбери вариант")

superuser_keyboard = InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin"), InlineKeyboardButton(text="Удалить админа ❌", callback_data="remove_admin")],
  [InlineKeyboardButton(text="➕ Добавить добавлятеля", callback_data="add_adder"), InlineKeyboardButton(text="Удалить добавлятеля ❌", callback_data="remove_adder")],
  [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user"), InlineKeyboardButton(text="Удалить пользователя ❌", callback_data="remove_user")],
  [InlineKeyboardButton(text="🌚 Показать список избранных 🌚", callback_data="show_favs")],
  [InlineKeyboardButton(text="📊 Загруженность сервера", callback_data="server_status"), InlineKeyboardButton(text="Получить копию БД 🗄", callback_data="get_db_backup")],
  [InlineKeyboardButton(text="📋 Получить копию логов 📋", callback_data="get_logs_backup")],
  [InlineKeyboardButton(text="🗄 Получить данные в виде таблицы 🗄", callback_data="get_data_excel")],
  [InlineKeyboardButton(text="➡️ Обновить расписание ⬅️", callback_data="update_timetable")],
  [InlineKeyboardButton(text="Назад ↩️", callback_data="back")]
])

adminka_keyboard = InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text="➕ Добавить добавлятеля", callback_data="add_adder"), InlineKeyboardButton(text="Удалить добавлятеля ❌", callback_data="remove_adder")],
  [InlineKeyboardButton(text="🌚 Показать список избранных 🌚", callback_data="show_favs")],
  [InlineKeyboardButton(text="Назад ↩️", callback_data="back")]
])

check_hw_before_apply_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Да ✅", callback_data="all_right")],
    [InlineKeyboardButton(text="🔄 Изменить предмет", callback_data="change_subject"), InlineKeyboardButton(text="Изменить задание 🔄", callback_data="change_task")],
    # [InlineKeyboardButton(text="🖼 Добавить фото 🖼", callback_data="add_photo")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back")]
  ]
)
remove_hw_by_id_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Да ✅", callback_data="delete_hw")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back")]
  ]
)

v_kakom_formatike_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="На день", callback_data="by_date"), InlineKeyboardButton(text="По предмету", callback_data="by_subject")],
  ]
)

back_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back")]
  ]
)

donate_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Поддержать", pay=True)],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="donate_cancel")]
]
)

async def allowed_subjects_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject}"))
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()

async def allowed_subjects_change_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject}-changed"))
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()

async def allowed_subjects_check_hw_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject}-check-hw"))
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()