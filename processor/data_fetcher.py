import datetime

from processor.model import Participant, MeetingInstance, Meeting, Attendance


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
            print(f"Response failed with code {response.status_code} for meeting {meeting_instance.uuid}")
            raise RuntimeError

        participants_json = response.json().get("participants")

        while token := response.json().get("next_page_token"):
            response = self.zoom.get_meeting_participants(meeting_instance.uuid, self.jwt_token, token)
            participants_json += response.json().get("participants")

        # Create Participants and store their Attendance
        participants = self.get_unique_participants(meeting_instance, participants_json)

        # Cache the results
        meeting_instance.cached = True
        meeting_instance.save()

        return participants

    def get_unique_participants(self, meeting_instance, participants_json):
        participants = []
        participant_names = set()
        for p in participants_json:
            participant, created = self.get_or_create_participant(p)
            if created:
                print(f"Found a new participant: {participant.name}: {participant.email}")
            if participant.name not in participant_names:
                participant_names.add(participant.name)
                participants.append(participant)
                Attendance.get_or_create(meeting_instance=meeting_instance,
                                         participant=participant)

        print(f"{len(participants)} unique participants.")
        return participants

    @staticmethod
    def get_or_create_participant(participant):
        if participant["user_email"] != "":
            # Detect name changes by same email
            return Participant.get_or_create(email=participant["user_email"],
                                             defaults={'user_id': participant["id"],
                                                       'name': participant["name"]})
        if participant["name"] != "":
            # If no email, fallback to just the name
            return Participant.get_or_create(name=participant["name"],
                                             defaults={'user_id': participant["id"],
                                                       'email': participant["user_email"]})
        return Participant.get_or_create(name=participant["name"],
                                         email=participant["user_email"],
                                         user_id=participant["id"])

    def fetch_meeting_details(self, meeting_id):
        meeting = Meeting.get_or_none(Meeting.meeting_id == meeting_id)
        if meeting is None:
            return self.fetch_meeting_details_from_zoom(meeting_id)
        return meeting

    def fetch_meeting_details_from_zoom(self, meeting_id):
        response = self.zoom.get_meeting_details(meeting_id, self.jwt_token)
        if not response.ok:
            print(f"Response failed with code {response.status_code} for meeting {meeting_id}")
            raise RuntimeError

        topic = response.json().get("topic")
        meeting, created = Meeting.get_or_create(meeting_id=meeting_id, topic=topic)

        print(f"Topic: {topic} participants.")
        return meeting

    @staticmethod
    def fetch_past_meeting_instances_cached(meeting):
        """
        We can't mark a Meeting object as cached, because they're not idempotent in the server.
        If we want to retrieve past meeting instances from DB, we must explicitly call this method.
        """
        return MeetingInstance.select().where(MeetingInstance.meeting == meeting)

    def fetch_past_meeting_instances(self, meeting):
        response = self.zoom.get_past_meeting_instances(meeting.meeting_id, self.jwt_token)
        if not response.ok:
            print(f"Response failed with code {response.status_code} for meeting {meeting.meeting_id}")
            raise RuntimeError

        meetings = response.json().get("meetings")
        meeting_instances = []
        for m in meetings:
            start_time_str = m["start_time"]
            start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%SZ')
            mi, created = MeetingInstance.get_or_create(uuid=m["uuid"], meeting=meeting,
                                                        defaults={'start_time': start_time})
            meeting_instances.append(mi)

        print(f"Found {len(meetings)} meeting instances for {meeting.meeting_id}")
        return meeting_instances
