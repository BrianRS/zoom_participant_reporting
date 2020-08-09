import os
import syslog

from processor.db_helper import DbHelper
from processor.model import Participant
from processor.zoom_helper import ZoomHelper


class DataFetcher:
    def __init__(self, db, zoom):
        self.db_helper = db
        self.zoom_helper = zoom
        self.jwt_token = zoom.generate_jwt_token()

    def fetch_meeting_participants(self, meeting_id):
        response = self.zoom_helper.get_meeting_participants(meeting_id, self.jwt_token)
        participants_json = response.json().get("participants")

        while token := response.json().get("next_page_token"):
            response = self.zoom_helper.get_meeting_participants(meeting_id, self.jwt_token, token)
            participants_json += response.json().get("participants")

        participants = []
        participant_ids = set()
        for p in participants_json:
            syslog.syslog(f"found {p}")
            participant = Participant.get_or_create(id=p["id"],
                                                    name=p["name"],
                                                    email=p["email"])
            if participant.id not in participant_ids:
                participant_ids.add(participant.id)
                participants += participant

        return participants


if __name__ == "__main__":
    db_helper = DbHelper("dev.db")

    zoom_api_key = os.environ.get("ZOOM_API_KEY")
    zoom_api_secret = os.environ.get("ZOOM_API_SECRET")
    zoom_helper = ZoomHelper(zoom_api_key, zoom_api_secret)

    fetcher = DataFetcher(db_helper, zoom_helper)

    zoom_meeting_id = os.environ.get("ZOOM_MEETING_ID")
    result = fetcher.fetch_meeting_participants(zoom_meeting_id)
