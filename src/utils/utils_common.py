import datetime
from components import line_bot_api
from utils import utils_database
import json

from linebot.models import (
    TextSendMessage,
)


def get_event_info(event):
    event_dict = event.message.as_json_dict()
    timestamp       = float(event.timestamp/1000)
    dt_object       = datetime.datetime.fromtimestamp(timestamp)
    datetime_string = dt_object.strftime("%Y-%m-%d %H:%M:%S")                     # 0.日期時間
    date_string     = dt_object.strftime("%Y-%m-%d")                                            # 1.日期
    time_string     = dt_object.strftime("%H:%M:%S")                                            # 2.時間
    session         = 'A' if float(time_string.replace(':', '')) < 12e4 else 'P' 
    source_type     = event.source.type
    group_id        = event.source.group_id if source_type == "group" else ""    # 4.群組ID
    summary         = line_bot_api.get_group_summary(group_id) if group_id != '' else ""
    group_name      = summary.group_name if group_id != '' else ""       # 5.群組名稱
    user_id         = event.source.user_id                                        # 6.傳訊者ID
    profile         = line_bot_api.get_group_member_profile(group_id, event.source.user_id) if group_id != '' else ""
    user_name       = profile.display_name        if group_id != '' else ""            # 7.傳訊者顯示名稱
    user_img        = profile.picture_url if group_id != '' else "" 
    msg_type        = event.message.type
    msg_id          = event.message.id
    image_set_id      = event_dict["imageSet"]["id"] if "imageSet" in event_dict.keys() else 'null'
    
    return {
        "source_type": source_type,
        "datetime": datetime_string,
        "date": date_string,
        "time": time_string,
        "session": session,
        "group_id": group_id,
        "group_name": group_name,
        "user_id": user_id,
        "user_name": user_name,
        "user_img": user_img,
        "msg_type": msg_type,
        "msg_id": msg_id,
        "image_set_id": image_set_id
    }


def get_img_count(img_event):
    def __check_is_image_set(img_event):
        return "imageSet" in img_event.message.as_json_dict().keys()
    
    is_image_set = __check_is_image_set(img_event)
    
    count = 0
    if is_image_set:
        index = img_event.message.image_set.index
        total = img_event.message.image_set.total
        db_is_image_set = utils_database.check_is_image_set_by_id(img_event.message.image_set.id)
        count = total if db_is_image_set else 0
    else:
        count = 1
        
    status = (True if count != 0 else False) or db_is_image_set
    reply_info = {
        "status": status,
        "img_count": count
    }
    return reply_info


def get_user_info(event):
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    return {
        "user_id": user_id,
        "display_name": profile.display_name,
        "picture_url": profile.picture_url
    }


def update_group_name():
    group_ids = utils_database.get_all_joined_groups()
    for group_id in group_ids:
        try:
            group_summary = line_bot_api.get_group_summary(group_id)
            group_name = group_summary.group_name
            status = utils_database.update_group_name_by_group_id(group_id=group_id, group_name=group_name)
        except Exception as e:
            utils_database.set_disbanded_group_by_group_id(group_id=group_id, note="已解散/disbanded")
    return {"status": True}


def linebot_send_text(reply_token, msg):
    message = TextSendMessage(text=msg)
    try:
        line_bot_api.reply_message(reply_token, message)
    except Exception as e:
        print("error: ", str(e))
    return
