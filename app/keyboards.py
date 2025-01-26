from utils.logger import logger
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.database.requests.subjects import get_subject_by_name

from copy import deepcopy

# start_keyboard_admin = ReplyKeyboardMarkup(keyboard=[
#   [KeyboardButton(text="👀 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
#   [KeyboardButton(text="❌ Удалить Д/З"), KeyboardButton(text="Админ-панель 😈")],
#   [KeyboardButton(text="🔄 Сбросить дедлайн Д/З 🔄")]
#   ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

# start_keyboard_adder = ReplyKeyboardMarkup(keyboard=[
#   [KeyboardButton(text="👀 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
# ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

# start_keyboard = ReplyKeyboardMarkup(keyboard=[
#   [KeyboardButton(text="👀 Посмотреть Д/З")]
# ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")

# Основные клавиатуры
start_keyboard_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📚 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
    [KeyboardButton(text="🗑️ Удалить Д/З"), KeyboardButton(text="Админ-панель ⚡")],
    [KeyboardButton(text="🔄 Сбросить дедлайн 🔄")]
], resize_keyboard=True, input_field_placeholder="Выберите действие")

start_keyboard_adder = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📚 Посмотреть Д/З"), KeyboardButton(text="Добавить Д/З ➕")],
    [KeyboardButton(text="🗑️ Удалить Д/З"), KeyboardButton(text="Сбросить дедлайн 🔄")],
    [KeyboardButton(text="👥 Моя группа")]
], resize_keyboard=True, input_field_placeholder="Выберите действие")

start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📚 Посмотреть Д/З"), KeyboardButton(text="👥 Моя группа")]
], resize_keyboard=True, input_field_placeholder="Выберите действие")

# Суперпользовательская клавиатура
superuser_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👑 Добавить админа", callback_data="add_admin"), InlineKeyboardButton(text="🗑️ Удалить админа", callback_data="remove_admin")],
    [InlineKeyboardButton(text="🌟 Добавить добавлятеля", callback_data="add_adder"), InlineKeyboardButton(text="🔻 Удалить добавлятеля", callback_data="remove_adder")],
    [InlineKeyboardButton(text="📥 Добавить пользователя", callback_data="add_user"), InlineKeyboardButton(text="📤 Удалить пользователя", callback_data="remove_user")],
    [InlineKeyboardButton(text="📜 Список избранных", callback_data="show_favs")],
    [InlineKeyboardButton(text="📢 Написать всем", callback_data="tell_all_users_call")],
    [InlineKeyboardButton(text="📊 Статистика сервера", callback_data="server_status")],
    [InlineKeyboardButton(text="🗃️ Резервная копия БД", callback_data="get_db_backup"), InlineKeyboardButton(text="📁 Получить логи", callback_data="get_logs_backup")],
    [InlineKeyboardButton(text="📊 Экспорт в Excel", callback_data="get_data_excel")],
    [InlineKeyboardButton(text="🔄 Обновить расписание", callback_data="update_timetable")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
])

# Админская клавиатура
adminka_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌟 Добавить добавлятеля", callback_data="add_adder"), 
     InlineKeyboardButton(text="🔻 Удалить добавлятеля", callback_data="remove_adder")],
    [InlineKeyboardButton(text="📜 Список избранных", callback_data="show_favs")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
])

# Клавиатура подтверждения
check_hw_before_apply_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="all_right")],
        [InlineKeyboardButton(text="📝 Изменить предмет", callback_data="change_subject"), InlineKeyboardButton(text="📝 Изменить задание", callback_data="change_task")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back")]
    ]
)

# Клавиатура управления группой
group_controller_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Ссылка для вступления", callback_data="get_group_link")],
        [InlineKeyboardButton(text="👥 Доб. добавлятеля", callback_data="add_user"), InlineKeyboardButton(text="🚫 Удал. добавлятеля", callback_data="remove_user")],
        [InlineKeyboardButton(text="🔄 Передать лидерство", callback_data="transfer_leadership")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]
)

# Клавиатура выбора дня
see_hw_keyboard = ReplyKeyboardMarkup(keyboard=[
  [KeyboardButton(text="📚 По предмету")],
  [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="📅 На завтра"), KeyboardButton(text="📅 На послезавтра")],
  [KeyboardButton(text="🗓 По дате"), KeyboardButton(text="◀️ Назад")],
], resize_keyboard=True, input_field_placeholder="Выбери период")

async def get_start_keyboard(user):
  admin_kb = deepcopy(start_keyboard_admin)
  adder_kb = deepcopy(start_keyboard_adder)
  default_kb = deepcopy(start_keyboard)

  user_role = user["role"]
  user_is_leader = user["is_leader"]

  user_keyboard = None

  match user_role:
    case 2:
      user_keyboard = adder_kb
    case 3 | 4:
      user_keyboard = admin_kb
    case _:
      user_keyboard = default_kb

  if user_is_leader:
    user_keyboard.keyboard.append([KeyboardButton(text="👑 Управление группой 👑")])

  return user_keyboard






remove_hw_by_id_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Да ✅", callback_data="delete_hw")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back")]
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

create_group_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="Создать группу ➕", callback_data="create_group")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back_to_start")]
]
)



do_join_to_group_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="✅ Присоединиться к группе", callback_data="join_group")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back_to_start")]
  ]
)

transfer_leadership_confirm_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="✅ Передать права лидерства", callback_data="transfer_leadership_confirm")],
    [InlineKeyboardButton(text="Отмена ❌", callback_data="back_to_start")]
  ]
)

async def get_settings_keyboard(notifications: bool):
  
  if notifications:
    notifications_btn = InlineKeyboardButton(text="Выключить рассылку расписания", callback_data="disable_notifications")
  else:
    notifications_btn = InlineKeyboardButton(text="Включить рассылку расписания", callback_data="enable_notifications")

  kb = InlineKeyboardBuilder()
  kb.add(notifications_btn)
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()

async def allowed_subjects_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    try:
      subject_id = (await get_subject_by_name(subject))["uid"]
      kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject_id}-add"))
    except Exception as e:
      logger.warning(f"Building keyboard ({subject}): {e}")
      pass
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()

async def allowed_subjects_change_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    try:
      subject_id = (await get_subject_by_name(subject))["uid"]
      kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject_id}-changed"))
    except Exception as e:
      logger.warning(f"Building keyboard ({subject}): {e}")
      pass
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()

async def allowed_subjects_check_hw_keyboard(subjects: list):
  kb = InlineKeyboardBuilder()
  for subject in subjects:
    try:
      subject_id = (await get_subject_by_name(subject))["uid"]
      kb.add(InlineKeyboardButton(text=subject, callback_data=f"{subject_id}-check-hw"))
    except Exception as e:
      logger.warning(f"Building keyboard ({subject}): {e}")
      pass
  kb.add(InlineKeyboardButton(text="Отмена ❌", callback_data="back"))
  return kb.adjust(1).as_markup()