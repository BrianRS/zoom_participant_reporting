import os
import sys

from processor.db_helper import DbHelper
from processor.model import Participant, MeetingInstance, Meeting, Attendance
from processor.zoom_helper import ZoomHelper


class DataFetcher:
    def __init__(self, db, zoom):
        self.db = db
        self.zoom = zoom
        self.jwt_token = zoom.generate_jwt_token()

    def fetch_meeting_participants(self, meeting_instance):
        if not meeting_instance.cached:
            return self.fetch_meeting_participants_from_zoom(meeting_instance)
        return Participant.select().join(Attendance).where(Attendance.meeting_instance == meeting_instance)

    def fetch_meeting_participants_from_zoom(self, meeting_instance):
        response = self.zoom.get_meeting_participants(meeting_instance.uuid, self.jwt_token)
        if not response.ok:
            sys.stderr.write(f"Response failed with code {response.status_code} for meeting {meeting_instance.uuid}")
            raise RuntimeError

        participants_json = response.json().get("participants")

        while token := response.json().get("next_page_token"):
            response = self.zoom.get_meeting_participants(meeting_instance.uuid, self.jwt_token, token)
            participants_json += response.json().get("participants")

        participants = []
        participant_ids = set()
        sys.stderr.write(f"\nReceived {len(participants_json)} participants.\n")

        # Create Participants and store their Attendance
        for p in participants_json:
            participant, created = Participant.get_or_create(user_id=p["id"],
                                                             name=p["name"],
                                                             email=p["user_email"])
            if participant.user_id not in participant_ids:
                sys.stderr.write(f"Found participant: {p}\n")
                participant_ids.add(participant.user_id)
                participants.append(participant)
            Attendance.get_or_create(meeting_instance=meeting_instance,
                                     participant=participant)

        sys.stderr.write(f"Found {len(participants)} unique participants.\n")

        # Cache the results
        meeting_instance.cached = True
        meeting_instance.save()

        return participants

    def fetch_past_meeting_instances(self, meeting):
        return self.fetch_past_meeting_instances_from_zoom(self, meeting)

    def fetch_past_meeting_instances_from_zoom(self, meeting):
        pass

    def fetch_meeting_details(self, meeting_id):
        meeting = Meeting.get_or_none(Meeting.meeting_id == meeting_id)
        if meeting is None:
            return self.fetch_meeting_details_from_zoom(meeting_id)
        return meeting

    def fetch_meeting_details_from_zoom(self, meeting_id):
        response = self.zoom.get_meeting_details(meeting_id, self.jwt_token)
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
