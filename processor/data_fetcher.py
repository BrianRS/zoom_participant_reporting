import os
import sys

from processor.db_helper import DbHelper
from processor.model import Participant, MeetingInstance, Meeting
from processor.zoom_helper import ZoomHelper


class DataFetcher:
    def __init__(self, db, zoom):
        self.db_helper = db
        self.zoom_helper = zoom
        self.jwt_token = zoom.generate_jwt_token()

    def fetch_meeting_participants(self, meeting_instance_id):
        return self.fetch_meeting_participants_from_zoom(meeting_instance_id)

    def fetch_meeting_participants_from_zoom(self, meeting_instance_id):
        response = self.zoom_helper.get_meeting_participants(meeting_instance_id, self.jwt_token)
        if not response.ok:
            sys.stderr.write(f"Response failed with code {response.status_code} for meeting {meeting_instance_id}")
            raise RuntimeError

        participants_json = response.json().get("participants")

        while token := response.json().get("next_page_token"):
            response = self.zoom_helper.get_meeting_participants(meeting_instance_id, self.jwt_token, token)
            participants_json += response.json().get("participants")

        participants = []
        participant_ids = set()
        sys.stderr.write(f"\nReceived {len(participants_json)} participants.\n")
        for p in participants_json:
            participant, created = Participant.get_or_create(user_id=p["id"],
                                                             name=p["name"],
                                                             email=p["user_email"])
            if participant.user_id not in participant_ids:
                sys.stderr.write(f"Found participant: {p}\n")
                participant_ids.add(participant.user_id)
                participants.append(participant)

        sys.stderr.write(f"Found {len(participants)} unique participants.\n")
        return participants

    def fetch_past_meetings(self, meeting_id):
        return self.fetch_past_meetings_from_zoom(self, meeting_id)

    def fetch_past_meetings_from_zoom(self, meeting_id):
        pass

    def fetch_meeting_details(self, meeting_id):
        #if Meeting.get(meeting_id)
        return self.fetch_meeting_details_from_zoom(meeting_id)

    def fetch_meeting_details_from_zoom(self, meeting_id):
        response = self.zoom_helper.get_meeting_details(meeting_id, self.jwt_token)
        if not response.ok:
            sys.stderr.write(f"Response failed with code {response.status_code} for meeting {meeting_id}")
            raise RuntimeError

        topic = response.json().get("topic")
        meeting, created = Meeting.get_or_create(meeting_id=meeting_id, topic=topic)

        sys.stderr.write(f"\nTopic: {topic} participants.\n")
        return meeting


if __name__ == "__main__":
    db_helper = DbHelper("dev.db")

    zoom_api_key = os.environ.get("ZOOM_API_KEY")
    zoom_api_secret = os.environ.get("ZOOM_API_SECRET")
    zoom_helper = ZoomHelper(zoom_api_key, zoom_api_secret)

    fetcher = DataFetcher(db_helper, zoom_helper)

    zoom_meeting_id = os.environ.get("ZOOM_MEETING_ID")
    result = fetcher.fetch_meeting_participants(zoom_meeting_id)
    for p in result:
        sys.stdout.write(str(p.name) + '\n')
