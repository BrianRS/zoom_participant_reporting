import math

import responses
import pandas as pd
import datetime as dt

from processor.model import Meeting
from processor.report_generator import ReportGenerator

from tests.conftest import make_meeting_instance, attend_meeting_with_new_participant
from tests.conftest import attend_meeting


def test_get_attendances(report_generator, data_fetcher, meeting, meeting_instance, mocker):
    # Generate test data
    mi_2 = make_meeting_instance(meeting, "second meeting")
    a, _ = attend_meeting_with_new_participant(meeting_instance, "a")
    b, _ = attend_meeting_with_new_participant(mi_2, "b")
    c, _ = attend_meeting_with_new_participant(mi_2, "c")

    mocker.patch.object(data_fetcher, "fetch_meeting_details")
    data_fetcher.fetch_meeting_details.return_value = meeting

    mocker.patch.object(data_fetcher, "fetch_past_meeting_instances")
    data_fetcher.fetch_past_meeting_instances.return_value = [meeting_instance, mi_2]

    mocker.patch.object(data_fetcher, "fetch_meeting_participants")
    data_fetcher.fetch_meeting_participants.side_effect = [[a], [b, c]]

    rep = report_generator.get_attendances(meeting.meeting_id)

    assert len(rep) == 2

    result_participants = rep[meeting_instance]
    assert 1 == len(result_participants)

    result_participants = rep[mi_2]
    assert 2 == len(result_participants)

    data_fetcher.fetch_meeting_details.assert_called_with(meeting.meeting_id)


@responses.activate
def test_report_generation(report_generator, meeting, meeting_instance, mocker):
    # Generate some test data
    mi_2 = make_meeting_instance(meeting, "second meeting instance id", start_time=dt.datetime(2020, 5, 18))
    a, _ = attend_meeting_with_new_participant(meeting_instance, "a")
    b, _ = attend_meeting_with_new_participant(mi_2, "b")
    c, _ = attend_meeting_with_new_participant(mi_2, "c")

    m2 = Meeting.create(meeting_id="meeting two", topic="meeting two topic")
    mi_3 = make_meeting_instance(m2, "third meeting instance id")
    attend_meeting(mi_3, b)

    attendance_m1 = {meeting_instance: [a], mi_2: [b, c]}
    attendance_m2 = {mi_3: [b]}

    # mock the call to get_participants_for_meeting
    mocker.patch.object(report_generator, "get_attendances")
    report_generator.get_attendances.side_effect = [attendance_m1, attendance_m2]

    df = report_generator.generate_report([meeting.meeting_id, m2.meeting_id])
    assert 10 == df.size

    assert 1 == df.at[meeting.meeting_id, "2020-05-17"]
    assert 1 == df.at[m2.meeting_id, "2020-05-17"]
    assert meeting.topic == df.at[meeting.meeting_id, 'Name']
    avg = df.at[meeting.meeting_id, ReportGenerator.AVG_COLUMN]
    assert math.isclose(1.5, avg, rel_tol=1e-5)
    avg = df.at[meeting.meeting_id, ReportGenerator.LAST_FOUR]
    assert math.isclose(1.5, avg, rel_tol=1e-5)

    assert 2 == df.at[meeting.meeting_id, "2020-05-18"]
    assert 0 == df.at[m2.meeting_id, "2020-05-18"]
    assert m2.topic == df.at[m2.meeting_id, 'Name']
    avg = df.at[m2.meeting_id, ReportGenerator.AVG_COLUMN]
    assert math.isclose(1.0, avg, rel_tol=1e-5)
    avg = df.at[m2.meeting_id, ReportGenerator.LAST_FOUR]
    assert math.isclose(1.0, avg, rel_tol=1e-5)


def test_dataframe_to_array():
    values_dict = {'Name': {'meeting_1': 'topic 1', 'meeting_2': 'topic 2'},
                   "2020-08-01": {'meeting_1': 1.0, 'meeting_2': 3.0},
                   "2020-08-02": {'meeting_1': 2.0, 'meeting_2': 0.0},
                   ReportGenerator.AVG_COLUMN: {'meeting_1': 1.5, 'meeting_2': 3.0},
                   ReportGenerator.LAST_FOUR: {'meeting_1': 1.5, 'meeting_2': 3.0}}
    df = pd.DataFrame(values_dict)
    expected = [['Meeting ID', 'Name', "2020-08-01", "2020-08-02",
                 ReportGenerator.AVG_COLUMN, ReportGenerator.LAST_FOUR],
                ['meeting_1', 'topic 1', 1.0, 2.0, 1.5, 1.5],
                ['meeting_2', 'topic 2', 3.0, '', 3.0, 3.0]]
    assert ReportGenerator.dataframe_to_array(df) == expected


def test_dataframe_to_array_sorted():
    values_dict = {'Name': {'meeting_1': 'topic 1', 'meeting_2': 'topic 2'},
                   "2020-08-01": {'meeting_1': 1.0, 'meeting_2': 3.0},
                   "2020-08-03": {'meeting_1': 3.0, 'meeting_2': 1.0},
                   "2020-08-02": {'meeting_1': 2.0, 'meeting_2': 0.0},
                   ReportGenerator.AVG_COLUMN: {'meeting_1': 2.0, 'meeting_2': 2.0},
                   ReportGenerator.LAST_FOUR: {'meeting_1': 2.0, 'meeting_2': 2.0}}
    df = pd.DataFrame(values_dict)
    expected = [['Meeting ID', 'Name', "2020-08-01", "2020-08-02", "2020-08-03",
                 ReportGenerator.AVG_COLUMN, ReportGenerator.LAST_FOUR],
                ['meeting_1', 'topic 1', 1.0, 2.0, 3.0, 2.0, 2.0],
                ['meeting_2', 'topic 2', 3.0, '', 1.0, 2.0, 2.0]]
    assert ReportGenerator.dataframe_to_array(df) == expected


@responses.activate
def test_last_four_average(report_generator, mocker):
    # Generate test data

    # Meeting 1
    m1 = Meeting.create(meeting_id="meeting one", topic="meeting one topic")
    mi_1_1 = make_meeting_instance(m1, "meeting instance 1_1", start_time=dt.datetime(2020, 5, 1))
    a, _ = attend_meeting_with_new_participant(mi_1_1, "a")

    mi_1_2 = make_meeting_instance(m1, "meeting instance 1_2", start_time=dt.datetime(2020, 5, 2))
    b, _ = attend_meeting_with_new_participant(mi_1_2, "b")
    c, _ = attend_meeting_with_new_participant(mi_1_2, "c")
    d, _ = attend_meeting_with_new_participant(mi_1_2, "d")
    e, _ = attend_meeting_with_new_participant(mi_1_2, "e")

    mi_1_3 = make_meeting_instance(m1, "meeting instance 1_3", start_time=dt.datetime(2020, 5, 3))
    mi_1_4 = make_meeting_instance(m1, "meeting instance 1_4", start_time=dt.datetime(2020, 5, 4))
    mi_1_5 = make_meeting_instance(m1, "meeting instance 1_5", start_time=dt.datetime(2020, 5, 5))

    # Meeting 2
    m2 = Meeting.create(meeting_id="meeting two", topic="meeting two topic")
    mi_2_1 = make_meeting_instance(m2, "meeting instance 2_1", start_time=dt.datetime(2020, 5, 1))
    mi_2_2 = make_meeting_instance(m2, "meeting instance 2_2", start_time=dt.datetime(2020, 5, 2))
    mi_2_3 = make_meeting_instance(m2, "meeting instance 2_3", start_time=dt.datetime(2020, 5, 3))

    # Simulate attendances
    attendance_m1 = {mi_1_1: [a], mi_1_2: [b, c], mi_1_3: [a, b], mi_1_4: [a, b], mi_1_5: [a, b, c, d, e]}
    attendance_m2 = {mi_2_1: [a], mi_2_2: [b], mi_2_3: [c]}

    # mock the call to get_participants_for_meeting
    mocker.patch.object(report_generator, "get_attendances")
    report_generator.get_attendances.side_effect = [attendance_m1, attendance_m2]

    df = report_generator.generate_report([m1.meeting_id, m2.meeting_id])

    assert 1 == df.at[m1.meeting_id, "2020-05-01"]
    assert 2 == df.at[m1.meeting_id, "2020-05-02"]
    assert 2 == df.at[m1.meeting_id, "2020-05-03"]
    avg = df.at[m1.meeting_id, ReportGenerator.AVG_COLUMN]
    assert math.isclose(2.4, avg, rel_tol=1e-5)
    avg = df.at[m1.meeting_id, ReportGenerator.LAST_FOUR]
    assert math.isclose(2.75, avg, rel_tol=1e-5)

    assert 1 == df.at[m2.meeting_id, "2020-05-01"]
    assert 1 == df.at[m2.meeting_id, "2020-05-02"]
    assert 1 == df.at[m2.meeting_id, "2020-05-03"]
    avg = df.at[m2.meeting_id, ReportGenerator.AVG_COLUMN]
    assert math.isclose(1.0, avg, rel_tol=1e-5)
    avg = df.at[m2.meeting_id, ReportGenerator.LAST_FOUR]
    assert math.isclose(1.0, avg, rel_tol=1e-5)

