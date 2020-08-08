from processor.db_helper import DbHelper
from processor.zoom_helper import ZoomHelper


def fetch_data(db, zoom):
    return 0


if __name__ == "__main__":
    db_helper = DbHelper("dev.db")
    zoom_helper = ZoomHelper("a")
    fetch_data(db_helper, zoom_helper)
