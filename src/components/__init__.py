from linebot import WebhookHandler
from linebot import LineBotApi
from constants import setting

line_bot_api = LineBotApi(setting.config_linebot["access_token"])
handler = WebhookHandler(setting.config_linebot["channel_secret"])
