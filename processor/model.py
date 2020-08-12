from peewee import *


class BaseModel(Model):
    pass


class Meeting(BaseModel):
    meeting_id = CharField(primary_key=True)
    topic = CharField()


class MeetingInstance(BaseModel):
    uuid = CharField(primary_key=True)
    meeting = ForeignKeyField(Meeting, backref='instances')
    start_time = DateTimeField()
    cached = BooleanField(default=False)


class Participant(BaseModel):
    user_id = CharField(index=True)
    name = CharField(null=True, index=True)
    email = CharField(null=True, index=True)


class Attendance(BaseModel):
    meeting_instance = ForeignKeyField(MeetingInstance, backref='attendances')
    participant = ForeignKeyField(Participant, backref='attendances')


class ExecutionLog(BaseModel):
    run_time = DateTimeField()
    exit_code = IntegerField()
