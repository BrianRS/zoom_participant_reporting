import pytest
import responses
import json
import datetime

from processor.model import Meeting, Participant
from tests.conftest import make_meeting_instance, attend_meeting_with_new_participant


@responses.activate
def test_get_participants_401(data_fetcher, meeting_instance):
    base = data_fetcher.zoom.reports_url
    responses.add(responses.GET, f"{base}/{meeting_instance.uuid}/participants?page_size=300",
                  json={'error': 'unauthorized'}, status=401)
    with pytest.raises(RuntimeError):
        data_fetcher.fetch_meeting_participants(meeting_instance)


@responses.activate
def test_get_participants(data_fetcher, meeting_instance):
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
    a, _ = attend_meeting_with_new_participant(meeting_instance, "Alice")
    b, _ = attend_meeting_with_new_participant(meeting_instance, "Bob")

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


@responses.activate
def test_fetch_past_meetings_zoom_401(data_fetcher, meeting):
    base = data_fetcher.zoom.past_meetings_url
    responses.add(responses.GET, f"{base}/{meeting.meeting_id}/instances",
                  json={'error': 'unauthorized'}, status=401)
    with pytest.raises(RuntimeError):
        data_fetcher.fetch_past_meeting_instances(meeting)


@responses.activate
def test_fetch_past_meeting_instances_from_zoom_success(data_fetcher, meeting):
    with open('tests/test_data/past_meetings.json') as f:
        data = json.load(f)
    base = data_fetcher.zoom.past_meetings_url
    responses.add(responses.GET, f"{base}/{meeting.meeting_id}/instances",
                  json=data, status=200)

    meetings = data_fetcher.fetch_past_meeting_instances(meeting)
    assert 7 == len(meetings)
    assert meetings[0].uuid == "7yQY89iC7e70Wj6Um03ULQ=="
    assert meetings[0].start_time == datetime.datetime(2020, 8, 1, 18, 6, 45)


@responses.activate
def test_fetch_past_meeting_existing_instance(data_fetcher, meeting):
    with open('tests/test_data/past_meetings.json') as f:
        data = json.load(f)
    base = data_fetcher.zoom.past_meetings_url
    responses.add(responses.GET, f"{base}/{meeting.meeting_id}/instances",
                  json=data, status=200)

    start_time = datetime.datetime(2020, 8, 16)
    meeting_instance_uuid = "7yQY89iC7e70Wj6Um03ULQ=="
    make_meeting_instance(meeting, meeting_instance_uuid, start_time)

    meetings = data_fetcher.fetch_past_meeting_instances(meeting)
    assert 7 == len(meetings)
    assert meetings[0].uuid == meeting_instance_uuid
    assert meetings[0].start_time == start_time


def test_get_past_meeting_instances_cache_hit(data_fetcher):
    meeting = Meeting.create(meeting_id=9, topic="9 topic", cached=True)
    meeting_instances = data_fetcher.fetch_past_meeting_instances_cached(meeting)

    make_meeting_instance(meeting)
    make_meeting_instance(meeting)

    assert 2 == len(meeting_instances)


@responses.activate
def test_detect_duplicate_names_in_meeting(data_fetcher, meeting_instance):
    with open('tests/test_data/past_participants_duplicates.json') as f:
        data = json.load(f)
    ps = data_fetcher.get_unique_participants(meeting_instance, data.get("participants"))

    assert 15 == len(ps)


def test_detect_name_change_same_email(data_fetcher, meeting_instance):
    with open('tests/test_data/past_participants_name_change.json') as f:
        data = json.load(f)
    ps = data_fetcher.get_unique_participants(meeting_instance, data.get("participants"))

    assert 14 == len(ps)


def test_does_not_create_new_participant_if_name_already_exists(data_fetcher, meeting_instance):
    data = [{"id": "1", "name": "Alice", "user_email": ""}]
    p = Participant.create(name="Alice", user_id="1")
    ps = data_fetcher.get_unique_participants(meeting_instance, data)

    assert 1 == len(ps)
    assert 1 == Participant.select().count()




