from fastapi import FastAPI
from sqladmin import Admin, ModelView
from app.database.models import User, Homework, Schedule, Media, Groups
from app.database.db_setup import async_engine, sync_engine

app = FastAPI()

admin = Admin(app, engine=async_engine, title="DomashkaBotDB Admin")

class UserAdmin(ModelView, model=User):
  name = "User"
  column_list = ["uid", "tg_id", "role", "username", "firstname", "lastname", "notifications","created_at", "updated_at", "group_id", "is_leader"]

class HomeworkAdmin(ModelView, model=Homework):
  name = "Homework"
  column_list = ["uid", "from_date", "subject", "task", "to_date", "group_id", "created_at", "added_by"]

class ScheduleAdmin(ModelView, model=Schedule):
  name = "Schedule"
  column_list = ["uid", "timestamp", "subject", "week_number"]

class MediaAdmin(ModelView, model=Media):
  name = "Media"
  column_list = ["uid", "homework_id", "media_id", "media_type"]

class GroupsAdmin(ModelView, model=Groups):
  name = "Group"

  column_list = ["uid", "course"]

admin.add_view(UserAdmin)
admin.add_view(HomeworkAdmin)
admin.add_view(ScheduleAdmin)
admin.add_view(MediaAdmin)
admin.add_view(GroupsAdmin)

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)