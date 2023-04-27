import dotenv
import os

dotenv.load_dotenv()

class Setting:
    def __init__(self):
        self.props = {}

    def __getattr__(self, name):
        return self.props[name]

    def __setattr__(self, name, value):
        if name == "props":
            object.__setattr__(self, name, value)
        else:
            self.props[name] = value
        return 


def get_config_setting():
    org = os.getenv("ORG")

    LINEBOT_CHANNEL_ACCESS_TOKEN = os.getenv("LINEBOT_CHANNEL_ACCESS_TOKEN")
    LINEBOT_CHANNEL_SECRET = os.getenv("LINEBOT_CHANNEL_SECRET")

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_database = os.getenv("DB_DATABASE")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    aws_bucket = os.getenv("AWS_BUCKET")

    setting = Setting()
    setting.org = org
    setting.bucket = aws_bucket

    setting.config_db = {
        "host": db_host,
        "port": int(db_port),
        "database": db_database,
        "user": db_user,
        "password": db_password
    }

    setting.config_linebot = {
        "access_token": LINEBOT_CHANNEL_ACCESS_TOKEN,
        "channel_secret": LINEBOT_CHANNEL_SECRET
    }
    return setting
    