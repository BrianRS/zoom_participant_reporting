import pytest
import uuid
import datetime
import random

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.google_helper import GoogleHelper
from processor.model import MeetingInstance, Meeting, Participant, Attendance
from processor.report_generator import ReportGenerator
from processor.zoom_helper import ZoomHelper


@pytest.fixture()
def zoom_helper():
    return ZoomHelper('https://test.example.com/v2', 'test_key', 'test_secret')


@pytest.fixture
def data_fetcher(zoom_helper):
    db = DbHelper(':memory:')
    return DataFetcher(db, zoom_helper)


@pytest.fixture
def meeting():
    meeting_id = str(random.randint(1, 2000))
    topic = f"topic for {meeting_id}"
    return Meeting.create(meeting_id=meeting_id, topic=topic)


@pytest.fixture
def meeting_instance(meeting):
    return make_meeting_instance(meeting)


class TestGoogleHelper():
    def __init__(self, service_account_file, scopes):
        self.service_account_file = service_account_file
        self.scopes = scopes


@pytest.fixture()
def google_helper(mocker):
    return TestGoogleHelper("test_file.json", [])


@pytest.fixture()
def report_generator(data_fetcher, google_helper):
    return ReportGenerator(data_fetcher, google_helper)


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


def attend_meeting_with_new_participant(meeting_instance, name, email=None):
    user_id = str(random.randint(5000, 10000))
    p = Participant.create(user_id=user_id, name=name)
    a = Attendance.create(meeting_instance=meeting_instance, participant=p)
    return p, a


def attend_meeting_with_existing_participant(meeting_instance, participant):
    return Attendance.create(meeting_instance=meeting_instance, participant=participant)

