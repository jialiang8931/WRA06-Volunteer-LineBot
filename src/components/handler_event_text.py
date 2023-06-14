from lambda_function import handler
from components import line_bot_api
import traceback

from utils.utils_common import get_event_info
from utils.utils_common import get_user_info
from utils.utils_common import update_group_name
from utils.utils_common import linebot_send_text
from utils import utils_database
from utils import utils_rainfall_event
from utils import utils_sp_actions
from utils.utils_reply_images import get_squad_patrol_record_msg_or_img
from utils import handler_routine_statistics

from linebot.models import (
    MessageEvent, 
    TextMessage, 
    ImageSendMessage
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    event_info = get_event_info(event)
    v_character = utils_database.get_user_position_by_user_id(user_id=event_info["user_id"])
    
    is_admin = True if v_character in ("管理者", "管理員") else False
    is_higher_user_right = True if v_character in ("承辦", "顧問", "隊員,顧問") else False
    is_team_leader = True if v_character in ("分隊長", "大隊長", "隊長") else False
    is_normal_user = True if v_character in ("隊員") else False

    user_msg = event.message.text
    is_user_msg = event.source.type == "user"
    is_group_msg = event.source.type == "group"

    first_char = user_msg[0]

    is_open_collect_record = first_char == "="
    is_get_user_id = first_char == ">"
    is_update_v_id_char = first_char == "$"
    is_search_v_id_record =  first_char == "-"
    is_search_squad_record = first_char == "+"
    is_update_v_record = first_char == "#"
    is_delete_v_record = first_char == "!"
    is_undo_del_v_record = first_char == "@"
    is_create_rainfall_event = first_char == "^"
    is_modify_rainfall_event = first_char == "~"


    try:

        if is_admin and is_user_msg and user_msg == "安安":
            user_info = get_user_info(event=event)
            msg = f"""【{ user_info["display_name"] }】你好，你的照片在這邊\n{ user_info["picture_url"] }"""
            linebot_send_text(event.reply_token, msg)
            return

        # 查找指令
        if (is_admin) and is_user_msg and user_msg == "指令":
            msg = "【查找指令】"
            msg += "\n" + "- 已允許收納的群組"
            msg += "\n" + "- 未允許收納的群組"
            msg += "\n" + "- 已解散棄用的群組"
            msg += "\n" + "- 近二十場豪雨事件"
            msg += "\n\n" + "【參數指令】" + "【時間格式】:YYYY-mm-DDTHH:MM:SS"
            msg += "\n" + '-【=】: { group_name }/{ allowance }: 修改特定群組之收納權限[t, f]'
            msg += "\n" + "-【>】: { org }/{ display_name }: 利用志工名稱取得相對應的 user_id"
            msg += "\n" + "-【$】: { org }/{ user_id }/{ v_id }: 藉由 org 及 user_id，設定 v_id"
            msg += "\n" + "-【+】: { 分隊名稱 }: 取得該分隊近兩月統計結果圖片"
            msg += "\n" + "-【-】: { v_id }: 取得該志工近兩月通報紀錄"
            msg += "\n" + '-【#】: { v_id }/{ 想改變的時間 }: 將管理者的在群組上傳的照片，變更為該志工的上傳紀錄'
            msg += "\n" + '-【!】: { org }{ v_id }/{ 起始時間 }/{ 結束時間 }: 刪除特定志工特定時段上傳紀錄'
            msg += "\n" + '-【@】: { org }{ v_id }/{ 起始時間 }/{ 結束時間 }: 回復特定志工特定時段被刪除的上傳紀錄'
            msg += "\n" + '-【^】: { rainfall_event_name }: 開設豪雨事件，並回傳該事件編號'
            msg += "\n" + '-【~】: { rainfall_event_id }/{ modify_type }/{ key words }: 新增/修改/刪除豪雨事件紀錄'
            msg += "\n" + '-----> type[ begin ]/{ 時間日期 }: 新增事件開設時間日期'
            msg += "\n" + '-----> type[ end ]/{ 時間日期 }: 新增事件結束時間日期'
            msg += "\n" + '-----> type[ title ]/{ 時間日期 }: 修改事件名稱'
            msg += "\n" + '-----> type[ note ]/{ 時間日期 }: 修改事件備註'
            msg += "\n" + '-----> type[ get ]: 取得該豪雨事件資料'
            msg += "\n" + '-----> type[ delete ]: 刪除該豪雨事件'
            linebot_send_text(event.reply_token, msg)
            return

        # 查找指令
        if (is_higher_user_right) and is_user_msg and user_msg == "指令":
            msg = "【查找指令】"
            msg += "\n" + "- 已允許收納的群組"
            msg += "\n\n" + "【參數指令】"
            msg += "\n" + "-【+】: { 分隊名稱 }: 取得該分隊近兩月統計結果圖片"
            msg += "\n" + "-【-】: { v_id }: 取得該志工近兩月通報紀錄"
            linebot_send_text(event.reply_token, msg)
            return
        
        # 更新所有使用者的 Profile
        if (is_admin) and is_user_msg and user_msg == "QQ123":
            status = utils_sp_actions.update_user_info()
            msg = status["msg"]
            linebot_send_text(event.reply_token, msg)
            return

        # 列出已參加群組
        if is_admin and is_user_msg and user_msg == "已允許收納的群組":
            msg = utils_database.get_target_allowance_group(allowance='true')
            linebot_send_text(event.reply_token, msg)
            return

        # 列出尚未允許的群組
        if is_admin and is_user_msg and user_msg == "未允許收納的群組":
            status_update_group_name = update_group_name()
            msg = utils_database._target_allowance_group(allowance='false')
            linebot_send_text(event.reply_token, msg)
            return

        # 列出已棄用的群組
        if is_admin and is_user_msg and user_msg == "已解散棄用的群組":
            status_update_group_name = update_group_name()
            msg = utils_database.get_disbanded_group()
            linebot_send_text(event.reply_token, msg)
            return

        # 列出近二十場豪雨事件
        if is_admin and is_user_msg and user_msg == "近二十場豪雨事件":
            status = utils_rainfall_event.get_recent_rainfalls()
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 創建豪雨事件
        if is_admin and is_user_msg and is_create_rainfall_event:
            title = user_msg[1:]
            status = utils_rainfall_event.create_rainfall_event_by_title(title=title)
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return
            
        # 對豪雨事件進行操作(by rainfall_event_id)
        if is_admin and is_user_msg and is_modify_rainfall_event:
            infos = user_msg[1:].split("/")
            rainfall_event_id = infos[0]
            modify_type = infos[1] 

            if modify_type == "get":
                status = utils_rainfall_event.get_rainfall_event_by_id(rainfall_event_id=rainfall_event_id)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "title":
                target_column = 'title'
                value = infos[2]
                status = utils_rainfall_event.update_target_column_value_by_rainfall_event_id(rainfall_event_id=rainfall_event_id, target_column=target_column, value=value)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "note":
                target_column = 'note'
                value = infos[2]
                status = utils_rainfall_event.update_target_column_value_by_rainfall_event_id(rainfall_event_id=rainfall_event_id, target_column=target_column, value=value)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "begin":
                target_column = 'begin'
                value = infos[2]
                status = utils_rainfall_event.update_target_datetime_value_by_rainfall_event_id(rainfall_event_id=rainfall_event_id, target_column=target_column, value=value)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "end":
                target_column = 'end'
                value = infos[2]
                status = utils_rainfall_event.update_target_datetime_value_by_rainfall_event_id(rainfall_event_id=rainfall_event_id, target_column=target_column, value=value)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "delete":
                target_column = 'status'
                value = "deleted"
                status = utils_rainfall_event.update_target_column_value_by_rainfall_event_id(rainfall_event_id=rainfall_event_id, target_column=target_column, value=value)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return

            if modify_type == "recover":
                status = utils_rainfall_event.recover_deleted_rainfall_event_by_id(rainfall_event_id=rainfall_event_id)
                msg = status["detail"]
                linebot_send_text(event.reply_token, msg)
                return
            
        # 管理者 - 打開群組收納權限
        if is_admin and is_user_msg and is_open_collect_record:
            infos = user_msg[1:].split("/")
            group_display_name = infos[0]
            allowance = 'true' if infos[1] in ('T', 't') else 'false'
            response = utils_database.update_group_allowance_by_name(display_name=group_display_name, allowance=allowance)
            msg = response["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 管理者 - 個人查詢 - 查詢志工名字的 user_id
        if is_admin and is_user_msg and is_get_user_id:
            infos = user_msg[1:].split("/")
            org = infos[0]
            display_name = infos[1]
            msg = utils_database.get_user_id_by_org_and_display_name(org=org, display_name=display_name)
            linebot_send_text(event.reply_token, msg)
            return

        # 管理者 - 個人查詢 - 新增群組志工的 v_id
        if is_admin and is_user_msg and is_update_v_id_char:
            infos = user_msg[1:].split("/")
            org = infos[0]
            user_id = infos[1]
            v_id = infos[2]
            status = utils_database.add_ingroup_user_v_id(org=org, user_id=user_id, v_id=v_id)
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 管理者 - 補缺漏照片
        if is_admin and is_user_msg and is_update_v_record:
            infos = user_msg[1:]
            infos = infos.split("/")
            v_id = infos[0]
            datetime_str = infos[1]
            status = utils_database.update_admin_post_record(v_id=v_id, datetime_str=datetime_str)
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 管理者 - 刪除特定志工特定時段照片
        if is_admin and is_user_msg and is_delete_v_record:
            infos = user_msg[1:]
            infos = infos.split("/")
            org = infos[0]
            v_id = infos[1]
            datetime_begin = infos[2]
            datetime_end = infos[3]
            status = utils_database.delete_admin_post_record(org=org, v_id=v_id, datetime_begin=datetime_begin, datetime_end=datetime_end)
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 管理者 - 回復特定志工特定時段照片
        if is_admin and is_user_msg and is_undo_del_v_record:
            infos = user_msg[1:]
            infos = infos.split("/")
            org = infos[0]
            v_id = infos[1]
            datetime_begin = infos[2]
            datetime_end = infos[3]
            status = utils_database.undo_delete_admin_post_record(org=org, v_id=v_id, datetime_begin=datetime_begin, datetime_end=datetime_end)
            msg = status["detail"]
            linebot_send_text(event.reply_token, msg)
            return

        # 業務相關人士 - 個人查詢 - 查詢個人通報紀錄(v_id)
        if (is_admin or is_higher_user_right) and is_user_msg and is_search_v_id_record:
            v_id = user_msg[1:]
            msg = utils_database.get_patrol_records_by_v_id(v_id)
            linebot_send_text(event.reply_token, msg)
            return

        # 業務相關人士 - 個人查詢 - 查詢分隊通報紀錄(分隊名稱)
        if (is_admin or is_higher_user_right) and is_user_msg and is_search_squad_record:
            target_squad_name = user_msg[1:]
            reply_info = get_squad_patrol_record_msg_or_img(target_squad_name)
            reply_type = reply_info["type"]
            if reply_type == "text":
                msg = reply_info["detail"]["msg"]
                linebot_send_text(event.reply_token, msg)

            if reply_type == "image":
                line_bot_api.reply_message(
                    event.reply_token, 
                    ImageSendMessage(
                        original_content_url=reply_info["detail"]["original_content_url"], 
                        preview_image_url=reply_info["detail"]["preview_image_url"]
                    )
                )
            return

        # 志工個人查詢 - 任何人
        if is_user_msg and user_msg == "個人通報查詢":
            msg = utils_database.get_patrol_records_by_user_id(event_info["user_id"])
            linebot_send_text(event.reply_token, msg)
            return

        if is_user_msg and user_msg == "近兩個月志工時數統計":
            # 一般隊員
            if is_normal_user:
                msg = handler_routine_statistics.get_personal_recent_2month_record(event_info["user_id"])
                linebot_send_text(event.reply_token, msg)
                return
            # 隊長
            if is_team_leader:
                target_squad_name = utils_database.get_squad_name_by_user_id(event_info["user_id"])
                reply_info = get_squad_patrol_record_msg_or_img(target_squad_name)
                reply_type = reply_info["type"]
                if reply_type == "text":
                    msg = reply_info["detail"]["msg"]
                    linebot_send_text(event.reply_token, msg)

                if reply_type == "image":
                    line_bot_api.reply_message(
                        event.reply_token, 
                        ImageSendMessage(
                            original_content_url=reply_info["detail"]["original_content_url"], 
                            preview_image_url=reply_info["detail"]["preview_image_url"]
                        )
                    )
                return

    except Exception as e:
        msg = "個人問答錯誤:" + user_msg + "\n" +str(e)
        msg += "\n" + str(traceback.format_exc())
        linebot_send_text(event.reply_token, msg)
        return

    # 群組只收關鍵字
    if is_group_msg:

        if not utils_database.check_is_allowed_collect_event_event_info_group(event.source.group_id):
            msg = "該群組尚未開通收納訊息功能，請向管理員申請權限，以便收納通報訊息"
            linebot_send_text(event.reply_token, msg)
            return 

        user_msg = event.message.text.upper()
        black_words = ["TABLE", "SELECT", "DATABASE", "DELETE", "UPDATE", "DROP", "CREATE", "EXISTS", "IF", ";"]
        for _word in black_words:
            user_msg = user_msg.replace(_word, "")

        specific_words = ["通報", "回報", "淹水", "下雨", "堆積", "淹", "巡查", "巡檢"]
        for _word in specific_words:
            if _word in user_msg:
                event_info.update({"content": user_msg})
                utils_database.insert_user_post_msg(event_info)
                break
        return
