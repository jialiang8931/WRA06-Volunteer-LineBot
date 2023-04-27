import datetime
from lambda_function import handler
from components import line_bot_api
from utils import utils_database

from linebot.models import (
    JoinEvent,
    MemberJoinedEvent, 
    MemberLeftEvent,
    TextSendMessage
)


@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    group_summary = line_bot_api.get_group_summary(group_id)
    event_info = {
        "group_id": group_summary.group_id,
        "group_name": group_summary.group_name,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    utils_database.insert_joined_group_info(event_info)

    if not utils_database.check_is_allowed_collect_event_event_info_group(event.source.group_id):
        msg = "該群組尚未開通收納訊息功能，請向管理員申請權限，以便收納通報訊息"
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)
        
    return


@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    group_id = event.source.group_id  
    summary = line_bot_api.get_group_summary(group_id)
    group_name = summary.group_name 
    user_id = event.joined.members[0].user_id
    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    display_name = profile.display_name 
    picture_url = profile.picture_url 

    event_info = {
        "datetime": current_dt,
        "group_id": group_id, 
        "group_name": group_name, 
        "user_id": user_id, 
        "display_name": display_name, 
        "picture_url": picture_url
    }
    
    try:
        utils_database.insert_user_info_when_join_group(event_info)
    except Exception as e:
        print(e)
        
    msg = f'嗨，{ display_name }\n歡迎您加入志工通報群組，本群組會收納所有您提供的通報訊息與照片，敬請避免在本群組聊天、傳送問候圖，感謝您的配合與諒解，也謝謝您熱心協助！'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    group_id = event.source.group_id
    user_id = event.left._members[0]["userId"]
    event_info = {
        "datetime": current_dt,
        "group_id": group_id,
        "user_id": user_id
    }
    status = utils_database.update_user_info_when_left_group(event_info)
    return status
