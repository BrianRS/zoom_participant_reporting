import pytest
import responses

from processor.zoom_helper import ZoomHelper

ZOOM = ZoomHelper('test_key', 'test_secret')


@responses.activate
def test_get_meeting_participants_401():
    responses.add(responses.GET, f"{ZOOM.base_url}/report/meetings/{1}/participants?page_size=300",
                  json={'error': 'unauthorized'}, status=401)
    r = ZOOM.get_meeting_participants(1, b'1')
    assert 401 == r.status_code


@responses.activate
def test_get_meeting_participants_success():
    responses.add(responses.GET, f"{ZOOM.base_url}/report/meetings/{2}/participants?page_size=300",
                  json={}, status=200)
    r = ZOOM.get_meeting_participants(2, b'2')
    assert 200 == r.status_code

@responses.activate
def test_get_meeting_details():
    assert 1 == 2


