import pytest
import responses
import json

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.zoom_helper import ZoomHelper

DB = DbHelper(':memory:')
ZOOM = ZoomHelper('test_key', 'test_secret')


def test_init():
    df = DataFetcher(DB, ZOOM)


@responses.activate
def test_get_participants_401(mocker):
    responses.add(responses.GET, f"{ZOOM.base_url}/report/meetings/{1}/participants?page_size=300",
                  json={'error': 'unauthorized'}, status=401)
    df = DataFetcher(DB, ZOOM)
    with pytest.raises(RuntimeError):
        ps = df.fetch_meeting_participants(1)


@responses.activate
def test_get_participants_success():
    with open('tests/past_participants_report.json') as f:
        data = json.load(f)

    responses.add(responses.GET, f"{ZOOM.base_url}/report/meetings/{2}/participants?page_size=300",
                  json=data, status=200)
    df = DataFetcher(DB, ZOOM)
    ps = df.fetch_meeting_participants(2)

    assert 20 == len(ps)

def test_get_participants_cached_hit():
    pass

#def test_get_participants_cached_fail():

#def test_get_meeting_details_from_zoom_fail():

#def test_get_meeting_details_from_zoom_success():


#def test_get_meeting_details_cached_fail():
#def test_get_meeting_details_cached_success():


#def test_get_past_meetings zoom-pass, zoom-fail, cached-fail, cached-success
