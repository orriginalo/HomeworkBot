import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database.models_old as old_models
import app.database.models as models
from app.database.db_setup import Base
from app.database.queries.other import sync_sequences

# Подключение к БД
OLD_DB_URL = "postgresql+psycopg2://domashkabot:domashkabot@10.242.106.91:5432/domashkabot"
NEW_DB_URL = "postgresql+psycopg2://domashkabot:domashkabot@localhost:5432/domashkabot"

old_engine = create_engine(OLD_DB_URL)
new_engine = create_engine(NEW_DB_URL)

OldSession = sessionmaker(bind=old_engine)
NewSession = sessionmaker(bind=new_engine)

old_session = OldSession()
new_session = NewSession()

# Создаем таблицы в новой БД (если не созданы)
Base.metadata.drop_all(new_engine)
Base.metadata.create_all(new_engine)

# === Перенос Groups ===
old_groups = old_session.query(old_models.Groups).all()
group_map = {}

for old_group in old_groups:
    new_group = models.Groups(
        uid=old_group.uid,
        name=old_group.name,
        course=old_group.course,
        ref_code=old_group.ref_code,
        is_equipped=old_group.is_equipped,
        leader_id=old_group.leader_id,
        member_count=old_group.member_count,
        created_at=old_group.created_at,
        updated_at=old_group.updated_at,
        subjects=old_group.subjects
    )
    new_session.add(new_group)
    group_map[old_group.uid] = new_group.uid

new_session.commit()

# === Перенос Users ===
old_users = old_session.query(old_models.User).all()

for old_user in old_users:
    new_user = models.User(
        uid=old_user.uid,
        tg_id=old_user.tg_id,
        role=old_user.role,
        username=old_user.username,
        firstname=old_user.firstname,
        lastname=old_user.lastname,
        settings=old_user.settings,
        created_at=old_user.created_at,
        updated_at=old_user.updated_at,
        moved_at=old_user.moved_at,
        group_uid=group_map.get(old_user.group_id),
        is_leader=old_user.is_leader
    )
    new_session.add(new_user)

new_session.commit()

# === Перенос Homework ===
old_homeworks = old_session.query(old_models.Homework).all()

for old_hw in old_homeworks:
    new_hw = models.Homework(
        uid=old_hw.uid,
        from_date=old_hw.from_date,
        subject=old_hw.subject,
        task=old_hw.task,
        to_date=old_hw.to_date,
        group_uid=group_map.get(old_hw.group_id),
        created_at=old_hw.created_at,
        user_uid=23
    )
    new_session.add(new_hw)

new_session.commit()

# === Перенос Schedule (структура не менялась) ===
old_schedule = old_session.query(old_models.Schedule).all()

for old_sch in old_schedule:
    new_sch = models.Schedule(
        uid=old_sch.uid,
        timestamp=old_sch.timestamp,
        group_name="-",
        subject=old_sch.subject,
        teacher="-",
        cabinet="-",
        week_number=old_sch.week_number,
        group_id=old_sch.group_id
    )
    new_session.add(new_sch)

new_session.commit()

# === Перенос Media (структура не менялась) ===
old_media = old_session.query(old_models.Media).all()

for old_m in old_media:
    new_m = models.Media(
        uid=old_m.uid,
        homework_id=old_m.homework_id,
        media_id=old_m.media_id,
        media_type=old_m.media_type
    )
    new_session.add(new_m)

new_session.commit()

# === Перенос Subjects (структура не менялась) ===
old_subjects = old_session.query(old_models.Subjects).all()

for old_subj in old_subjects:
    new_subj = models.Subjects(
        uid=old_subj.uid,
        name=old_subj.name
    )
    new_session.add(new_subj)

new_session.commit()

# === Перенос Settings (структура не менялась) ===
old_settings = old_session.query(old_models.Settings).all()

for old_set in old_settings:
    new_set = models.Settings(
        uid=old_set.uid,
        key=old_set.key,
        value=old_set.value
    )
    new_session.add(new_set)

new_session.commit()

asyncio.run(sync_sequences())

print("Миграция завершена!")
