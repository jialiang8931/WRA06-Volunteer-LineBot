from linebot import WebhookHandler
from linebot import LineBotApi

from .configuration import get_config_setting


setting = get_config_setting()
line_bot_api = LineBotApi(setting.config_linebot["access_token"])
handler = WebhookHandler(setting.config_linebot["channel_secret"])
