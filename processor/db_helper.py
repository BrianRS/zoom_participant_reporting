from peewee import *
import processor.model as m

TABLES = [m.Meeting,
          m.MeetingInstance,
          m.Attendance,
          m.Participant,
          m.ExecutionLog,
          ]


class DbHelper:
    def __init__(self, db_name):
        self.db = SqliteDatabase(db_name)
        self.db.connect()
        self.db.bind(TABLES)
        self.db.create_tables(TABLES)
