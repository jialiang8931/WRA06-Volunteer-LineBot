import boto3
from io import BytesIO
import datetime

from lambda_function import handler
from components import line_bot_api
from utils.utils_common import get_event_info, get_img_count
from utils import utils_database
from components import setting 

from linebot.models import (
    MessageEvent, 
    ImageMessage, 
    TextSendMessage,
)
s3 = boto3.client('s3')

@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event): 
    if not utils_database.check_is_allowed_collect_event_event_info_group(event.source.group_id):
        msg = "該群組尚未開通收納訊息功能，請向管理員申請權限，以便收納通報訊息"
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)
        return 
        
    if event.source.type == "group":
        print("      " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  ---->  我是老六，我正在處理群組照片訊息")
        event_info = get_event_info(event)
        
        # Following block is trying to handle binary file and produce the link of file.
        message_content  = line_bot_api.get_message_content(event.message.id)
        image_content = message_content.content
        file_obj = BytesIO(image_content)

        month_string = event_info["date"].replace('-', "")
        key = f"""images/records/{ event_info["group_id"] }/{ event_info["user_id"] }/{ month_string }/{ event_info["msg_id"] }.jpg"""

        try:
            s3.upload_fileobj(file_obj, setting.bucket, key)
            event_info.update({"content": key})
            utils_database.insert_user_post_msg(event_info)
        except Exception as e:
            msg = "[ERROR] 儲存照片那邊錯誤 " + str(e)
            print(msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        # ==============================================================     
        # ================== 以下處理傳照片後的訊息 ======================
        # ==============================================================
        try:
            reply_info = get_img_count(event)
            # 假如照片不是最後一張，就直接return掉
            if not reply_info["status"]: 
                return
            # 假如照片是最後一張
            profile = line_bot_api.get_group_member_profile(event_info["group_id"], event_info["user_id"])
            user_name = profile.display_name
    
            greeting_msg = ""
            _hour_time = int(event_info["time"][:2])
            if _hour_time >= 5 and _hour_time < 12:
                greeting_msg = "早上"
            if _hour_time >= 12 and _hour_time < 14:
                greeting_msg = "中午"
            if _hour_time >= 14 and _hour_time < 18:
                greeting_msg = "下午"
            if _hour_time >= 18 and _hour_time < 24:
                greeting_msg = "晚上"
            if _hour_time >= 0 and _hour_time < 5:
                greeting_msg = "晚上"
                
            if reply_info["img_count"] != 0:
                msg = f"""{ user_name }先進，{ greeting_msg }好\n{ event_info["datetime"] }\n上傳 { reply_info["img_count"] } 張照片\n老六已將照片收納至資料庫"""
            else:
                msg = f"""{ user_name }先進，{ greeting_msg }好\n{ event_info["datetime"] }\n老六已將您巡檢的照片收納至資料庫"""
                
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        except Exception as e:
            msg = "[ERROR] 回復照片數量那邊錯誤 " + str(e)
            print(msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    return
        