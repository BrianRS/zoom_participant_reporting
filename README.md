## What This Code Does
1. Retrieves meeting attendance data from Zoom API and creates a report from it.
2. Uploads the report to a Google Drive Spreadsheet.

## How To Install It
    brew install python git pipenv
    
    git clone https://github.com/BrianRS/zoom_participant_reporting.git

## How To Run It
1. Create a file, ``meetings.txt`` with the list of Zoom meeting IDs you'd like to report on. One meeting ID per line.

2. Make sure to have the Zoom API Key and Secret, see [here](https://medium.com/swlh/how-i-automate-my-church-organisations-zoom-meeting-attendance-reporting-with-python-419dfe7da58c) for how to get these.

3. Run:

        pipenv shell
    
        export PYTHONPATH=.
        export ZOOM_API_KEY=**Put API key here**
        export ZOOM_API_SECRET=**Put API secret here**
        python processor/report_generator.py prod.db raw_data/meetings.txt


## Additional Info
See ``docs/`` for detailed examples on debugging meeting data

