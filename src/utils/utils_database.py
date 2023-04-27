from typing import List, Dict
from components.do_transaction_pg import do_transaction_command_manage, get_dict_data_from_database
from components import setting 
from functools import reduce
import datetime



def insert_joined_group_info(event_info: Dict):
    """
        event_info = {
            "group_id": group_id, 
            "group_name": group_name, 
            "datetime": current_dt,
        }
    """

    group_id = event_info["group_id"]
    group_name = event_info["group_name"]
    datetime_join = event_info["datetime"]

    sql_string = f"""
        INSERT INTO volunteer.linebot_joined_groups(
            group_id, group_name, datetime_join)
            VALUES ('{ group_id }', '{ group_name }', '{ datetime_join }');
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": "Insert group info already."}
    except Exception as e:
        print(e)
        return {"status": False, "detail": "Insert group info failed."}


def check_is_allowed_collect_event_event_info_group(group_id: str) -> bool:
    sql_string = f"""
        SELECT group_id
        FROM volunteer.linebot_joined_groups
        WHERE collected_msg = true;
    """
    group_ids = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    group_ids = [_["group_id"] for _ in group_ids]
    is_in_allowed_group = group_id in group_ids
    return is_in_allowed_group


def insert_user_info_when_join_group(event_info: Dict):
    """
        event_info = {
            "datetime": current_dt,
            "group_id": group_id, 
            "group_name": group_name, 
            "user_id": user_id, 
            "display_name": display_name, 
            "picture_url": picture_url
        }
    """
    
    group_id = event_info["group_id"]
    group_name = event_info["group_name"]
    org = setting.org
    user_id = event_info["user_id"]
    display_name = event_info["display_name"]
    picture_url = event_info["picture_url"]
    datetime = event_info["datetime"]

    sql_string = f"""
        INSERT INTO volunteer.v_ingroup(
            group_id, group_name, org, user_id, display_name, picture_url, datetime_join)
            VALUES ('{ group_id }', '{ group_name }', '{ org }', '{ user_id }', '{ display_name }', '{ picture_url }', '{ datetime }')
        ON CONFLICT DO NOTHING
        ;
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": "Insert ingroup user info already."}
    except Exception as e:
        print(e)
        return {"status": False, "detail": "Insert ingroup user info failed."}


def update_user_info_when_left_group(event_info: Dict):
    """
        event_info = {
            "datetime": current_dt,
            "group_id": group_id,
            "user_id": user_id
        }
    """
    sql_string = f"""
        UPDATE volunteer.v_ingroup
            SET datetime_leave='{ event_info["datetime"] }'
            WHERE group_id = '{ event_info["group_id"] }'
                AND user_id = '{ event_info["user_id"] }'
        ;
    """
    do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
    return {"status": True, "detail": "Updated member left event already."}


def insert_user_post_msg(event_info: Dict):
    """
        event_info = {   
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
            "content": content,
            "image_set_id": event_info["image_set_id"]
        }
    """
    image_set_id = f"""'{ event_info["image_set_id"] }'""" if event_info["image_set_id"] != 'null' else 'null'

    sql_string = f'''
        INSERT INTO volunteer.v_msgs(
            datetime, date, "time", session, group_id, user_id, msg_type, msg_id, content, image_set_id)
            VALUES ('{ event_info["datetime"] }', '{ event_info["date"] }', '{ event_info["time"] }', 
                    '{ event_info["session"] }', '{ event_info["group_id"] }', '{ event_info["user_id"] }', 
                    '{ event_info["msg_type"] }', '{ event_info["msg_id"] }', '{ event_info["content"] }', { image_set_id }
            ) ON CONFLICT DO NOTHING
            ;
    '''
    try:
        print(sql_string)
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": "Insert user msg already."}
    except Exception as e:
        print(e)
        return {"status": False, "detail": "Insert user msg failed."}


def get_user_id_by_org_and_display_name(org: str, display_name: str, v_id: str = "QQ123"):
    sql_string = f"""
        SELECT user_id
            , display_name
            , picture_url 
            , datetime_join
        FROM volunteer.v_ingroup
        WHERE org = '{ org }'
            AND display_name ILIKE '%{ display_name }%'
        ;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)

    data_string = [f"""加入時間: { record["datetime_join"] }
        大頭貼: { record["picture_url"] }
        更新指令: ${ org }/{ record["user_id"] }/{ v_id }
    """
    for record in data]

    data_string = "\n========\n".join(data_string).replace("  ", "")
    return data_string


def add_ingroup_user_v_id(org: str, user_id: str, v_id: str):
    sql_string = f"""
        UPDATE volunteer.v_ingroup
            SET v_id = '{ v_id }'
            WHERE org = '{ org }'
                AND user_id ILIKE '%{ user_id }%'
        ;
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"【更新完成】 \n **// { org } / { user_id } / { v_id } //**"}
    except Exception as e:
        print(e)
        return {"status": False, "detail": f"【更新失敗】 \n{ org }=>{ user_id }=> { v_id }"}


def get_patrol_records_by_v_id(v_id: str, org: str = setting.org):
    sql_string = f"""SELECT user_id, display_name FROM volunteer.v_ingroup WHERE v_id = '{ v_id }' AND org IN ('{ org }', 'TTL'); """
    return_data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    user_id = return_data[0]['user_id'] if len(return_data) > 0 else ""
    user_name = return_data[0]['display_name'] if len(return_data) > 0 else ""
    if user_id == "": 
        msg_content = f'{ v_id }: 並未登載到 "volunteer".v_ingroup'
    if user_id != "": 
        sql_string = f'''
            SELECT to_char(date, 'yyyy-mm-dd') as date, to_char(MIN(datetime), 'hh24:mi:ss') as time, COUNT(date) FROM volunteer.v_msgs
            WHERE datetime = ( 
                SELECT MAX(datetime) FROM volunteer.v_msgs
                WHERE msg_type = 'update'
                    AND user_id = '{ user_id }'
                    AND date >= DATE_TRUNC('month', CURRENT_DATE) - interval '1 month'
                ) 
                AND content = '1'
            GROUP BY date

            UNION
            SELECT to_char(date, 'yyyy-mm-dd') as date, to_char(MIN(datetime), 'hh24:mi:ss') as time, COUNT(date) FROM volunteer.v_msgs
            WHERE msg_type = 'image'
                AND user_id = '{ user_id }' 
                AND date >= DATE_TRUNC('month', CURRENT_DATE) - interval '1 month'
            GROUP BY date
        ;
        '''
        data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        data.sort(key = lambda x: x["date"])
        msg_content = reduce(lambda x, record: f"{x}\n{record['date']}，共{record['count']}張照片", data, f'{ "您已於以下時間通報成功" }')

        msg_content = msg_content if len(msg_content) > 13 else "近兩個月並無您的通報紀錄。"
        msg_content = f'【{ user_name }】 / { v_id } / { user_id }\n' + msg_content
    return msg_content


def get_patrol_records_by_user_id(user_id: str, org: str = setting.org):
    sql_string = f"""SELECT v_id, user_id, display_name FROM volunteer.v_ingroup WHERE user_id = '{ user_id }' AND org IN ('{ org }', 'TTL'); """
    return_data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    v_id = return_data[0]['v_id'] if len(return_data) > 0 else ""
    user_name = return_data[0]['display_name'] if len(return_data) > 0 else ""

    sql_string = f'''
        SELECT to_char(date, 'yyyy-mm-dd') as date, to_char(MIN(datetime), 'hh24:mi:ss') as time, COUNT(date) FROM volunteer.v_msgs
        WHERE datetime = ( 
            SELECT MAX(datetime) FROM volunteer.v_msgs
            WHERE msg_type = 'update'
                AND user_id = '{ user_id }'
                AND date >= DATE_TRUNC('month', CURRENT_DATE) - interval '1 month'
            ) 
            AND content = '1'
        GROUP BY date

        UNION
        SELECT to_char(date, 'yyyy-mm-dd') as date, to_char(MIN(datetime), 'hh24:mi:ss') as time, COUNT(date) FROM volunteer.v_msgs
        WHERE msg_type = 'image'
            AND user_id = '{ user_id }' 
            AND date >= DATE_TRUNC('month', CURRENT_DATE) - interval '1 month'
        GROUP BY date
    ;
    '''
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    data.sort(key = lambda x: x["date"])
    msg_content = reduce(lambda x, record: f"{x}\n{record['date']}，共{record['count']}張照片", data, f'{ "您已於以下時間通報成功" }')

    msg_content = msg_content if len(msg_content) > 13 else "近兩個月並無您的通報紀錄。"
    msg_content = f'【{ v_id }】 { user_name }\n' + msg_content
    return msg_content


def update_admin_post_record(v_id: str, datetime_str: str = "2023-02-16T12:00:12"):
    sql_string = f"SELECT user_id FROM volunteer.v_ingroup WHERE v_id = '{ v_id }'"
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    if data == []:
        return {"status": False, "detail": f"無此 v_id ({ v_id })"}
    session = "A" if int(datetime_str.split("T")[1][:2]) <= 12 else "P"
    sql_string = f"""
        WITH manager_ids AS (
                    SELECT manage_v_user_id.user_id FROM volunteer.v_ingroup as manage_v_user_id
                    INNER JOIN (
                            SELECT v_id FROM volunteer.v_list
                            WHERE v_character LIKE '%管理%'
                        ) AS manage_v_id
                    ON manage_v_user_id.v_id = manage_v_id.v_id
                ),
            target_user_id AS (
                    SELECT user_id FROM volunteer.v_ingroup WHERE v_id = '{ v_id }' LIMIT 1
                ),
            manager_upload_imgs AS (
                    SELECT * FROM volunteer.v_msgs
                    WHERE datetime >= NOW() - INTERVAL '10 minutes'
                        AND msg_type = 'image'
                        AND user_id IN (SELECT user_id FROM manager_ids)
            )
        UPDATE volunteer.v_msgs
        SET user_id = (SELECT user_id FROM target_user_id)
            , datetime = TIMESTAMP '{ datetime_str }'
            , date = TIMESTAMP '{ datetime_str }'
            , "time" = TIMESTAMP '{ datetime_str }'
            , session = ' { session } '
        WHERE datetime IN (SELECT datetime FROM manager_upload_imgs)
            AND user_id IN (SELECT user_id FROM manager_ids)
        ;
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"更新成功紀錄至{ v_id }"}

    except Exception as e:
        return {"status": False, "detail": f"錯誤，{ str(e) }"}


def delete_admin_post_record(org: str, v_id: str, datetime_begin: str, datetime_end: str):
    sql_string = f"""
        WITH target_user_id AS (
                    SELECT user_id FROM volunteer.v_ingroup 
                    WHERE v_id = '{ v_id }' AND org = '{ org }'
                    LIMIT 1
                ),
            target_msgs AS (
                    SELECT * FROM volunteer.v_msgs
                    WHERE datetime BETWEEN TIMESTAMP '{ datetime_begin }' AND TIMESTAMP '{ datetime_end }'
                        AND msg_type = 'image'
                        AND user_id IN (SELECT user_id FROM target_user_id)
            )
        UPDATE volunteer.v_msgs
            SET msg_type = 'del/image'
        WHERE datetime IN (SELECT datetime FROM target_msgs)
            AND user_id IN (SELECT user_id FROM target_msgs)
        ;    
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功刪除紀錄: { v_id }/{ datetime_begin }/{ datetime_end }"}

    except Exception as e:
        return {"status": False, "detail": f"刪除紀錄失敗: { str(e) }"}


def undo_delete_admin_post_record(org: str, v_id: str, datetime_begin: str, datetime_end: str):
    sql_string = f"""
        WITH target_user_id AS (
                    SELECT user_id FROM volunteer.v_ingroup 
                    WHERE v_id = '{ v_id }' AND org = '{ org }'
                    LIMIT 1
                ),
            target_msgs AS (
                    SELECT * FROM volunteer.v_msgs
                    WHERE datetime BETWEEN TIMESTAMP '{ datetime_begin }' AND TIMESTAMP '{ datetime_end }'
                        AND msg_type = 'del/image'
                        AND user_id IN (SELECT user_id FROM target_user_id)
            )
        UPDATE volunteer.v_msgs
            SET msg_type = 'image'
        WHERE datetime IN (SELECT datetime FROM target_msgs)
            AND user_id IN (SELECT user_id FROM target_msgs)
        ;    
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功復原紀錄: { v_id }/{ datetime_begin }/{ datetime_end }"}

    except Exception as e:
        return {"status": False, "detail": f"復原紀錄失敗: { str(e) }"}


def get_user_position_by_user_id(user_id: str):
    sql_string = f"""
        WITH ingroup_v_id AS (
                SELECT v_id
                FROM volunteer.v_ingroup
                WHERE user_id = '{ user_id }'
            ),
            
            v_list_character AS (
                SELECT v_character FROM volunteer.v_list
                WHERE v_id IN (SELECT * FROM ingroup_v_id)
                AND year = 2023
            )            
        SELECT * FROM v_list_character LIMIT 1;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    v_character = data[0]["v_character"] if len(data) > 0 else "一般使用者"
    return v_character


def get_user_display_name_by_uuid(user_id: str):
    sql_string = f"""
        SELECT display_name FROM volunteer.v_ingroup
        WHERE user_id = '{ user_id }';
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    user_display_name = data[0]["display_name"] if len(data) > 0 else "您"
    return user_display_name


def get_squad_name_by_user_id(user_id: str):
    sql_string = f"""
        WITH v_ingroup_v_id AS (
                SELECT v_id FROM volunteer.v_ingroup
                WHERE user_id = '{ user_id }'
            ),
            
            v_squad AS (
                SELECT 
                    COALESCE(squad, '有在群組，但無登載至v_list') AS squad 
                FROM volunteer.v_list
                WHERE EXISTS (
                    SELECT 1 FROM v_ingroup_v_id
                    WHERE v_ingroup_v_id.v_id = volunteer.v_list.v_id
                        AND volunteer.v_list.year = 2023
                )
            )
        SELECT * FROM v_squad LIMIT 1
        ;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    squad_name = data[0]["squad"] if len(data) > 0 else "查無分隊"
    return squad_name

def update_group_allowance_by_name(display_name, allowance):
    sql_string = f"""
        UPDATE volunteer.linebot_joined_groups
            SET collected_msg= { allowance }
            WHERE group_name LIKE '%{ display_name }%';
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功更改{ display_name }群組收納權限=> { allowance }"}

    except Exception as e:
        return {"status": False, "detail": f"更改群組收納權限失敗: { display_name }群組權限=> { allowance }"}


def get_target_allowance_group(allowance):    
    sql_string = f"""
        SELECT group_id, group_name, datetime_join, collected_msg, COALESCE(note, '') note
            FROM volunteer.linebot_joined_groups
        WHERE collected_msg = { allowance } 
        ORDER BY datetime_join DESC;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    title = "已允許收納之群組:" if allowance == "true" else "未允許收納之群組:"
    title = title if len(data) != 0 else "無"
    for _group in data:
        if "disbanded" in _group["note"]: continue
        title += f"""\n{ _group["datetime_join"] }-> { _group["group_name"] }"""
    title = title if title != "未允許收納之群組:" else "無"
    return title


def update_group_name_by_group_id(group_id: str, group_name: str):
    sql_string = f"""
        UPDATE volunteer.linebot_joined_groups
            SET group_name = '{ group_name }'
            WHERE group_id = '{ group_id }';
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, }
    except Exception as e:
        return {"status": False}


def set_disbanded_group_by_group_id(group_id: str, note: str):
    sql_string = f"""
        UPDATE volunteer.linebot_joined_groups
            SET collected_msg = false, note = '{ note }'
            WHERE group_id = '{ group_id }';
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, }
    except Exception as e:
        return {"status": False}

def get_all_joined_groups():
    sql_string = f"""
        SELECT group_id FROM volunteer.linebot_joined_groups;
    """
    try:
        data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        group_ids = [_["group_id"] for _ in data]
        return group_ids
    except Exception as e:
        return []

def get_disbanded_group():
    sql_string = f"""
        SELECT group_id, group_name, datetime_join, collected_msg, note
            FROM volunteer.linebot_joined_groups
        WHERE note ILIKE '%/disbanded%'
        ORDER BY datetime_join DESC;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    title = "已棄用之群組:" 
    title = title if len(data) != 0 else "無"
    for _group in data:
        title += f"""\n{ _group["datetime_join"] }-> { _group["group_name"] }"""
    return title
    
    
    
def check_is_image_set_by_id(image_set_id):
    sql_string = f"""
        SELECT COUNT(image_set_id) AS count
        FROM volunteer.v_msgs
        WHERE image_set_id IS NOT null
        	AND image_set_id = '{ image_set_id }'
        ;
    """
    data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    is_image_set = data[0]["count"] == 1
    return is_image_set
    