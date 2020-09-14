import sys
import os
import pandas as pd
import datetime

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.report_generator import ReportGenerator
from processor.zoom_helper import ZoomHelper


class ParticipantReportGenerator(ReportGenerator):
    def __init__(self, data_fetcher, google_helper):
        super().__init__(data_fetcher, google_helper)
        self.data_fetcher = data_fetcher
        self.google = google_helper

    def generate_report(self, meeting_ids):
        df = pd.DataFrame(data=[], columns=[ReportGenerator.TOPIC_COLUMN])
        for meeting_id in meeting_ids:
            attendances = self.get_attendances(meeting_id)
            meeting = self.data_fetcher.fetch_meeting_details(meeting_id)
            for meeting_instance, participants in attendances.items():
                # We will use the dates as the column names
                # and the meeting id's and topics as the row names
                date = meeting_instance.start_time.date().strftime('%Y-%m-%d')
                df.loc[meeting_id, date] = self.get_participants_string(participants)
            df.loc[meeting_id, ReportGenerator.TOPIC_COLUMN] = meeting.topic

        df = df.fillna('')
        return df

    @staticmethod
    def get_participants_string(participants):
        names = [p.name for p in participants]
        #if "CircleAnywhere Sessions Evens" in names: names.remove("CircleAnywhere Sessions Evens")
        #if "CircleAnywhere Sessions Odds" in names: names.remove("CircleAnywhere Sessions Odds")
        return ", ".join(names)


def main():
    db_name = sys.argv[1]
    meeting_ids_file = sys.argv[2]
    zoom_api_key = os.environ["ZOOM_API_KEY"]
    zoom_api_secret = os.environ["ZOOM_API_SECRET"]

    meeting_ids = None
    with open(meeting_ids_file) as f:
        meeting_ids = f.read().splitlines()
        print(f"Generating participant report for {len(meeting_ids)} meetings")

    db = DbHelper(db_name)

    zoom = ZoomHelper(ReportGenerator.ZOOM_URL, zoom_api_key, zoom_api_secret)

    data_fetcher = DataFetcher(db, zoom)
    rg = ParticipantReportGenerator(data_fetcher, None)
    report = rg.generate_report(meeting_ids)

    run_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
    export_file = f'participants_{run_date}.csv'
    report.to_csv(export_file, index=True, header=True)


if __name__ == "__main__":
    main()
