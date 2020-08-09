import pytest
import responses
import json
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


@pytest.fixture()
def meeting_instance():
    meeting_id = str(random.randint(1, 2000))
    topic = f"topic for {meeting_id}"
    meeting_instance_id = uuid.uuid1()
    start_time = datetime.datetime(2020, 5, 17)
    Meeting.create(meeting_id=meeting_id, topic=topic)
    meeting_instance = MeetingInstance.create(uuid=meeting_instance_id,
                                              meeting_id=meeting_id,
                                              start_time=start_time,
                                              cached=False)
    return meeting_instance


def attend_meeting(meeting_instance, name, email=None):
    user_id = str(random.randint(5000, 10000))
    p = Participant.create(user_id=user_id, name=name)
    a = Attendance.create(meeting_instance=meeting_instance, participant=p)
    return p, a


@responses.activate
def test_get_participants_401(data_fetcher, meeting_instance):
    base = data_fetcher.zoom.reports_url
    responses.add(responses.GET, f"{base}/{meeting_instance.uuid}/participants?page_size=300",
                  json={'error': 'unauthorized'}, status=401)
    with pytest.raises(RuntimeError):
        data_fetcher.fetch_meeting_participants(meeting_instance)


@responses.activate
def test_get_participants_unique(data_fetcher, meeting_instance):
    with open('tests/test_data/past_participants_report.json') as f:
        data = json.load(f)

    base = data_fetcher.zoom.reports_url
    responses.add(responses.GET,
                  f"{base}/{meeting_instance.uuid}/participants?page_size=300",
                  json=data, status=200)
    ps = data_fetcher.fetch_meeting_participants(meeting_instance)

    assert 20 == len(ps)
    assert meeting_instance.cached


def test_get_participants_cache_hit_no_participants(data_fetcher, meeting_instance):
    meeting_instance.cached = True
    meeting_instance.save()

    ps = data_fetcher.fetch_meeting_participants(meeting_instance)
    assert 0 == len(ps)


def test_get_participants_cache_hit_some_participants(data_fetcher, meeting_instance):
    meeting_instance.cached = True
    meeting_instance.save()
    a, _ = attend_meeting(meeting_instance, "Alice")
    b, _ = attend_meeting(meeting_instance, "Bob")

    ps = data_fetcher.fetch_meeting_participants(meeting_instance)
    assert 2 == len(ps)
    assert ps[0].user_id == a.user_id
    assert ps[1].user_id == b.user_id


@responses.activate
def test_get_meeting_details_from_zoom_401(data_fetcher):
    base = data_fetcher.zoom.reports_url
    meeting_id = 14
    responses.add(responses.GET, f"{base}/{meeting_id}",
                  json={'error': 'unauthorized'}, status=401)
    with pytest.raises(RuntimeError):
        data_fetcher.fetch_meeting_details(meeting_id)


@responses.activate
def test_fetch_meeting_details_from_zoom_success(data_fetcher):
    meeting_id = 15
    with open('tests/test_data/meeting_details.json') as f:
        data = json.load(f)
    responses.add(responses.GET, f"{data_fetcher.zoom.reports_url}/{meeting_id}",
                  json=data, status=200)

    meeting = data_fetcher.fetch_meeting_details(meeting_id)
    assert meeting.meeting_id == meeting_id
    assert meeting.topic == "2 hr Awesome Meeting Saturday 1:00 pm CDT / 8:15 pm CEST"


def test_get_meeting_details_cached_hit(data_fetcher):
    Meeting.create(meeting_id=13, topic="13 topic")
    meeting = data_fetcher.fetch_meeting_details(13)
    assert '13' == meeting.meeting_id
    assert "13 topic" == meeting.topic


# def test_get_past_meetings zoom-pass, zoom-fail, cached-fail, cached-success
