from peewee import *


class BaseModel(Model):
    pass


class Meeting(BaseModel):
    id = UUIDField(primary_key=True)
    name = CharField()


class MeetingInstance(BaseModel):
    uuid = UUIDField(primary_key=True)
    meeting_id = ForeignKeyField(Meeting, backref='instances')
    start_time = DateTimeField()


class Participant(BaseModel):
    id = UUIDField(index=True)
    name = CharField(null=True, index=True)
    email = CharField(null=True, index=True)


class Attendance(BaseModel):
    meeting_instance_uuid = ForeignKeyField(MeetingInstance, backref='attendances')
    participant_id = ForeignKeyField(Participant, backref='attendances')


class ExecutionLog(BaseModel):
    run_time = DateTimeField()
    exit_code = IntegerField()
