import sys

import pytest
import responses
from processor.report_generator import ReportGenerator

from tests.conftest import make_meeting_instance, attend_meeting


def test_get_all_participants_meeting(data_fetcher, meeting, meeting_instance, mocker):
    rg = ReportGenerator(data_fetcher)

    mi_2 = make_meeting_instance(meeting, "second meeting")
    a, _ = attend_meeting(meeting_instance, "a")
    b, _ = attend_meeting(mi_2, "b")
    c, _ = attend_meeting(mi_2, "c")

    mocker.patch.object(data_fetcher, "fetch_meeting_details")
    data_fetcher.fetch_meeting_details.return_value = meeting

    mocker.patch.object(data_fetcher, "fetch_past_meeting_instances")
    data_fetcher.fetch_past_meeting_instances.return_value = [meeting_instance, mi_2]

    mocker.patch.object(data_fetcher, "fetch_meeting_participants")
    data_fetcher.fetch_meeting_participants.side_effect = [[a], [b, c]]

    rep = rg.get_all_participants_for_meeting(meeting.meeting_id)

    assert 2 == len(rep)

    result_participants = rep[meeting_instance]
    assert 1 == len(result_participants)

    result_participants = rep[mi_2]
    assert 2 == len(result_participants)

    data_fetcher.fetch_meeting_details.assert_called_with(meeting.meeting_id)


