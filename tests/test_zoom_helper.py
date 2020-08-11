import responses


@responses.activate
def test_get_meeting_participants_401(zoom_helper):
    responses.add(responses.GET, f"{zoom_helper.base_url}/report/meetings/{1}/participants?page_size=300",
                  json={'error': 'unauthorized'}, status=401)
    r = zoom_helper.get_meeting_participants(1, b'1')
    assert 401 == r.status_code


@responses.activate
def test_get_meeting_participants_success(zoom_helper):
    responses.add(responses.GET, f"{zoom_helper.base_url}/report/meetings/{2}/participants?page_size=300",
                  json={}, status=200)
    r = zoom_helper.get_meeting_participants(2, b'2')
    assert 200 == r.status_code


@responses.activate
def test_get_meeting_details_success(zoom_helper):
    responses.add(responses.GET, f"{zoom_helper.base_url}/report/meetings/{2}",
                  json={}, status=200)
    r = zoom_helper.get_meeting_details(2, b'2')
    assert 200 == r.status_code


@responses.activate
def test_get_meeting_participants_401(zoom_helper):
    responses.add(responses.GET, f"{zoom_helper.base_url}/report/meetings/{1}",
                  json={'error': 'unauthorized'}, status=401)
    r = zoom_helper.get_meeting_details(1, b'1')
    assert 401 == r.status_code
