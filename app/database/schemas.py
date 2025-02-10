from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from datetime import datetime

class UserSchema(BaseModel):
  uid: Optional[int]
  tg_id: int
  role: int = Field(ge=0, le=4)
  username: Optional[str]
  firstname: Optional[str]
  lastname: Optional[str]
  settings: dict
  created_at: datetime
  updated_at: datetime
  moved_at: Optional[datetime]
  group_uid: Optional[int]
  is_leader: bool
  
class UserRelSchema(UserSchema):
    group: Optional["GroupSchema"]
    homeworks: Optional[list["HomeworkRelSchema"]]
  
class HomeworkSchema(BaseModel):
  uid: Optional[int]
  from_date: datetime
  subject: str
  task: Optional[str]
  to_date: Optional[datetime]
  group_uid: int
  created_at: datetime
  user_uid: int

class HomeworkRelSchema(HomeworkSchema):
  group: Optional["GroupSchema"]
  user: Optional["UserSchema"]
  
class GroupSchema(BaseModel):
  uid: Optional[int]
  name: str
  course: Optional[int]
  ref_code: Optional[str]
  is_equipped: bool
  leader_id: Optional[int]
  member_count: int
  created_at: datetime
  updated_at: datetime
  subjects: Optional[List[str]]

class ScheduleSchema(BaseModel):
  uid: Optional[int]
  timestamp: datetime
  subject: str
  week_number: int
  group_id: Optional[int]

class MediaSchema(BaseModel):
  uid: Optional[int]
  homework_id: int
  media_id: str
  media_type: str
  
class SubjectSchema(BaseModel):
  uid: Optional[int]
  name: str
  
class SettingsSchema(BaseModel):
  uid: Optional[int]
  key: str
  value: str