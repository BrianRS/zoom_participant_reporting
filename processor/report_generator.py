import os
import sys
from typing import Dict, List

from pandas import DataFrame
import pandas as pd

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.google_helper import GoogleHelper
from processor.model import MeetingInstance, Participant
from processor.zoom_helper import ZoomHelper

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"]


class ReportGenerator:
    def __init__(self, data_fetcher, google_helper):
        self.data_fetcher = data_fetcher
        self.google = google_helper

    def get_attendances(self, meeting_id) -> Dict[MeetingInstance, List[Participant]]:
        """
        For any meeting, returns a Dict[MeetingInstance, List[Participant]]
        """
        meeting = self.data_fetcher.fetch_meeting_details(meeting_id)
        past_meetings = self.data_fetcher.fetch_past_meeting_instances(meeting)
        result = {}

        for mi in past_meetings:
            participants = self.data_fetcher.fetch_meeting_participants()
            result[mi] = participants

        return result

    def generate_report(self, meeting_ids):
        meetings = {}
        for meeting_id in meeting_ids:
            attendances = self.get_attendances(meeting_id)
            for meeting_instance, participants in attendances.items():
                column = meeting_instance.start_time.date()
                try:
                    meetings[column][meeting_id] = len(participants)
                except KeyError:
                    meetings[column] = {meeting_id: len(participants)}

        print("\n")
        print(meetings)
        df: DataFrame = pd.DataFrame(meetings, dtype=pd.Int64Dtype())
        df = df.fillna(0)
        print(df)
        return df


def main():
    db_name = sys.argv[1]
    meeting_ids_file = sys.argv[2]
    zoom_api_key = os.environ.get("ZOOM_API_KEY")
    zoom_api_secret = os.environ.get("ZOOM_API_SECRET")

    meeting_ids = None
    with open(meeting_ids_file) as f:
        meeting_ids = f.readlines()
        print(f"Generating report for {len(meeting_ids)} meetings")

    db = DbHelper(db_name)

    zoom = ZoomHelper("https://api.zoom.us/v2", zoom_api_key, zoom_api_secret)

    service_account_file = f".secrets/{os.listdir('.secrets')[0]}"
    google_helper = GoogleHelper(service_account_file, SCOPES)

    fetcher = DataFetcher(db, zoom)

    df = DataFetcher(db, zoom)
    rg = ReportGenerator(df, google_helper)
    report = rg.generate_report(meeting_ids)
    # TODO put into google drive


if __name__ == "__main__":
    main()

