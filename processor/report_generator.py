import os
import sys
import datetime
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
AVG_COLUMN = 'Average'


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

        # Add average attendance
        avg = df.mean(skipna=True, numeric_only=True, axis=1)
        df[AVG_COLUMN] = avg

        df = df.fillna(0)
        return df

    @staticmethod
    def dataframe_to_array(df):
        rows, cols = df.shape

        names = df.pop(TOPIC_COLUMN)
        averages = df.pop(AVG_COLUMN)
        values_dict = df.to_dict()

        # Create all the rows, and add one for the headers row
        values = [['Meeting ID', TOPIC_COLUMN]]

        # Populate the content of header row up to the dates
        header_row = 0

        # Populate the first and second columns (Meeting Ids, Names) across all rows
        row_name_to_num = {}
        row_counter = 1
        for meeting_id, name in names.iteritems():
            # Add a row for each meeting
            row = [meeting_id, name]
            values.append(row)

            # Keep a mapping of each row name to its position
            row_name_to_num[meeting_id] = row_counter
            row_counter += 1

        # Sort the dates
        dates = list(values_dict.keys())
        dates.sort()

        for date in dates:
            date_values = values_dict[date]
            values[header_row].append(date)
            # Add all the attendance numbers for each date
            for row_name, value in date_values.items():
                row = row_name_to_num[row_name]
                if value == 0:
                    value = ''
                values[row].append(value)

        # Add the average at the end of the row
        values[header_row].append(AVG_COLUMN)
        for meeting_id, avg in averages.iteritems():
            row_num = row_name_to_num[meeting_id]
            values[row_num].append(avg)

        return values

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

    data_fetcher = DataFetcher(db, zoom)
    rg = ReportGenerator(data_fetcher, google_helper)
    report = rg.generate_report(meeting_ids)
    values = rg.dataframe_to_array(report)

    run_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

    return rg.upload_report(values, run_date)


if __name__ == "__main__":
    main()

