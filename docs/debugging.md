## Get Summary Statistics

    pipenv shell
    python
    
    from processor.model import *
    from processor.db_helper import DbHelper
    db = DbHelper("prod.db")
    
    Meeting.select().count()
    MeetingInstance.select().count()
    Attendance.select().count()
    Participant.select().count()

## Create zoom connection

    zoom_api_key = <key>
    zoom_api_secret = <secret>
    
    from processor.zoom_helper import ZoomHelper
    from processor.data_fetcher import DataFetcher
    zoom = ZoomHelper("https://api.zoom.us/v2", zoom_api_key, zoom_api_secret)
    data_fetcher = DataFetcher(db, zoom)


## Checking participants for a Meeting

    meeting_id = <meeting id>
    m = Meeting.select().where(Meeting.meeting_id==meeting_id).first()

## Get latest instance of the meeting

    mi = MeetingInstance.select().where(MeetingInstance.meeting == m).order_by(MeetingInstance.start_time.desc()).first()
    
    data_fetcher.fetch_meeting_participants(mi)
    data_fetcher.fetch_meeting_participants_from_zoom(mi)


