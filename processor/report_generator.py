import os
import sys
import datetime
import json
from typing import Dict, List

import pandas as pd
from googleapiclient.errors import HttpError

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.google_helper import GoogleHelper
from processor.model import MeetingInstance, Participant
from processor.zoom_helper import ZoomHelper

SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive.metadata"]
TOPIC_COLUMN = 'Name'


class ReportGenerator:
    def __init__(self, data_fetcher, google_helper):
        self.data_fetcher = data_fetcher
        self.google = google_helper

    def get_attendances(self, meeting_id) -> Dict[MeetingInstance, List[Participant]]:
        """
        For any meeting, returns a Dict[MeetingInstance, List[Participant]]
        """
        print(f"\nGetting meeting details for {meeting_id}")
        meeting = self.data_fetcher.fetch_meeting_details(meeting_id)
        print(f"Meeting name: {meeting.topic}")
        past_meetings = self.data_fetcher.fetch_past_meeting_instances(meeting)
        result = {}

        for mi in past_meetings:
            participants = self.data_fetcher.fetch_meeting_participants(mi)
            result[mi] = participants

        return result

    def generate_report(self, meeting_ids):
        df = pd.DataFrame(data=[], columns=[TOPIC_COLUMN])
        for meeting_id in meeting_ids:
            attendances = self.get_attendances(meeting_id)
            meeting = self.data_fetcher.fetch_meeting_details(meeting_id)
            for meeting_instance, participants in attendances.items():
                # We will use the dates as the column names
                # and the meeting id's and topics as the row names
                date = meeting_instance.start_time.date().strftime('%Y-%m-%d')
                df.loc[meeting_id, date] = len(participants)
            df.loc[meeting_id, TOPIC_COLUMN] = meeting.topic

        df = df.fillna(0)
        return df

    def upload_report(self, report, run_date):
        output_file = f"zoom_report_{run_date}"
        folder_id = self.google.get_folder_id("CA Reports")

        sheet_id = self.google.create_new_sheet(output_file, folder_id)
        result = self.google.insert_df_to_sheet(sheet_id, report)
        sheet_link = self.google.get_sheet_link(result.get("spreadsheetId"))
        print(f"Finished uploading Zoom report.\n"
              f"spreadsheetId: {result.get('updates').get('spreadsheetId')}\n"
              f"updatedRange: {result.get('updates').get('updatedRange')}\n"
              f"updatedRows: {result.get('updates').get('updatedRows')}\n"
              f"link: {sheet_link}")
        return sheet_link


def main():
    db_name = sys.argv[1]
    meeting_ids_file = sys.argv[2]
    zoom_api_key = os.environ["ZOOM_API_KEY"]
    zoom_api_secret = os.environ["ZOOM_API_SECRET"]

    meeting_ids = None
    with open(meeting_ids_file) as f:
        meeting_ids = f.read().splitlines()
        print(f"Generating report for {len(meeting_ids)} meetings")

    db = DbHelper(db_name)

    zoom = ZoomHelper("https://api.zoom.us/v2", zoom_api_key, zoom_api_secret)

    service_account_file = f".secrets/{os.listdir('.secrets')[0]}"
    google_helper = GoogleHelper(service_account_file, SCOPES)

    fetcher = DataFetcher(db, zoom)

    df = DataFetcher(db, zoom)
    rg = ReportGenerator(df, google_helper)
    report = rg.generate_report(meeting_ids)

    run_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

    return rg.upload_report(report, run_date)


if __name__ == "__main__":
    main()

