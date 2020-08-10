import pytest
import uuid
import datetime
import random

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.model import MeetingInstance, Meeting, Participant, Attendance
from processor.zoom_helper import ZoomHelper


@pytest.fixture
def data_fetcher():
    db = DbHelper(':memory:')
    zoom = ZoomHelper('test_key', 'test_secret')
    return DataFetcher(db, zoom)


@pytest.fixture
def meeting():
    meeting_id = str(random.randint(1, 2000))
    topic = f"topic for {meeting_id}"
    return Meeting.create(meeting_id=meeting_id, topic=topic)


@pytest.fixture
def meeting_instance(meeting):
    return make_meeting_instance(meeting)


def make_meeting_instance(meeting, meeting_instance_id=None, start_time=None):
    if meeting_instance_id is None:
        meeting_instance_id = uuid.uuid1()
    if start_time is None:
        start_time = datetime.datetime(2020, 5, 17)
    meeting_instance = MeetingInstance.create(uuid=meeting_instance_id,
                                              meeting=meeting,
                                              start_time=start_time,
                                              cached=False)
    return meeting_instance


def attend_meeting(meeting_instance, name, email=None):
    user_id = str(random.randint(5000, 10000))
    p = Participant.create(user_id=user_id, name=name)
    a = Attendance.create(meeting_instance=meeting_instance, participant=p)
    return p, a

