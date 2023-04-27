import json
from linebot.exceptions import InvalidSignatureError  
from components import handler, line_bot_api

from components.handler_event_group import handler
from components.handler_event_text import handler
from components.handler_event_image import handler

def lambda_handler(event, context):

    try:
        signature = event['headers']['x-line-signature']
        body = event['body']
        handler.handle(body, signature)

    except:
        return {
            'statusCode': 502,
            'body': json.dumps("\u4f60\u5abd\u5c41\u80a1\u8b9a")
            }
    return {
        'statusCode': 200,
        'body': json.dumps("Hello from Lambda!")
        }
