import os

from processor.data_fetcher import DataFetcher
from processor.db_helper import DbHelper
from processor.zoom_helper import ZoomHelper


class ReportGenerator:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    def get_all_participants_for_meeting(self, meeting_id):
        """
        For any meeting, returns a Dict[MeetingInstance, [Participants]]
        """
        meeting = self.data_fetcher.fetch_meeting_details(meeting_id)
        past_meetings = self.data_fetcher.fetch_past_meeting_instances(meeting)
        result = {}

        for mi in past_meetings:
            participants = self.data_fetcher.fetch_meeting_participants()
            result[mi] = participants

        # TODO put into google drive

        return result


if __name__ == "__main__":
    db = DbHelper("dev.db")

    zoom_api_key = os.environ.get("ZOOM_API_KEY")
    zoom_api_secret = os.environ.get("ZOOM_API_SECRET")
    zoom = ZoomHelper(zoom_api_key, zoom_api_secret)

    fetcher = DataFetcher(db_helper, zoom_helper)

    zoom_meeting_id = os.environ.get("ZOOM_MEETING_ID")
    db = "dev.db"
    df = DataFetcher(db, zoom)
    rg = ReportGenerator(df)
    rg.generate_report()
