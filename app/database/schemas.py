from pydantic import BaseModel, Field
from typing import Optional, List
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
  group_id: Optional[int]
  group_name: Optional[str]
  is_leader: bool

class HomeworkSchema(BaseModel):
  uid: Optional[int]
  from_date: datetime
  subject: str
  task: Optional[str]
  to_date: Optional[datetime]
  group_id: int
  created_at: datetime
  added_by: Optional[int]

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
  timestamp: int
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