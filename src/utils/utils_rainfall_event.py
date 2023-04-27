from typing import List, Dict
from components.do_transaction_pg import do_transaction_command_manage, get_dict_data_from_database
from components import setting 
import datetime


def get_recent_rainfalls():
    sql_string = f"""
        SELECT id
            , COALESCE(title, '') title
            , datetime_record 
        FROM volunteer.v_rainfall_events 
        WHERE status != 'deleted' OR status IS NULL
        ORDER BY id DESC
        LIMIT 20;
    """
    try:
        data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        _event = [f"""【{ _["id"] }】【{ _["title"] }】【{ _["datetime_record"] }】""" for _ in data]
        msg = "\n".join(_event)
        msg = msg if msg != "" else "無資料"
        return {
            "status": True,
            "detail": msg,
            "data": data
        }
    except Exception as e:
        return {
            "status": False,
            "detail": str(e)
        }


def get_rainfall_event_by_id(rainfall_event_id: int):
    sql_string = f"""
        SELECT id
            , COALESCE(title, '') title
            , datetime_record 
            , datetime_begin
            , datetime_end
            , COALESCE(note, '') note
        FROM volunteer.v_rainfall_events 
        WHERE id = { rainfall_event_id }
            AND (status != 'deleted' OR status IS NULL)
    """
    try:
        data = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        msg = ""
        if data != []:
            _data = data[0]
            msg += f"""事件編號: { _data["id"] }"""
            msg += f"""\n事件名稱: { _data["title"] }"""
            msg += f"""\n開設時間: { _data["datetime_record"] }"""
            msg += f"""\n開始時間: { _data["datetime_begin"] }"""
            msg += f"""\n結束時間: { _data["datetime_end"] }"""
            msg += f"""\n事件備註: { _data["note"] }"""
        msg = msg if msg != "" else "無此豪雨事件資料"
        return {
            "status": True,
            "detail": msg
        }
    except Exception as e:
        return {
            "status": False,
            "detail": str(e)
        }


def update_target_column_value_by_rainfall_event_id(rainfall_event_id, target_column, value):
    sql_string = f"""
        UPDATE volunteer.v_rainfall_events
            SET { target_column } = '{ value }'
        WHERE id = { rainfall_event_id }
            AND (status != 'deleted' OR status IS NULL)
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功設定事件編號【{ rainfall_event_id }】【{ target_column }】【{ value }】"}
    except Exception as e:
        return {"status": False, "detail": f"錯誤: { str(e) }"}


def update_target_datetime_value_by_rainfall_event_id(rainfall_event_id, target_column, value):
    sql_string = f"""
        UPDATE volunteer.v_rainfall_events
            SET datetime_{ target_column } = TIMESTAMP '{ value }'
        WHERE id = { rainfall_event_id }
            AND (status != 'deleted' OR status IS NULL)
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功設定事件編號【{ rainfall_event_id }】【datetime_{ target_column }】【{ value }】"}
    except Exception as e:
        return {"status": False, "detail": f"錯誤: { str(e) }"}


def recover_deleted_rainfall_event_by_id(rainfall_event_id):
    sql_string = f"""
        UPDATE volunteer.v_rainfall_events
            SET status = 'on'
        WHERE id = { rainfall_event_id }
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        return {"status": True, "detail": f"成功回復被刪除豪雨事件，編號【{ rainfall_event_id }】"}
    except Exception as e:
        return {"status": False, "detail": f"錯誤: { str(e) }"}


def create_rainfall_event_by_title(title):
    datetime_record = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sql_string = f"""
        INSERT INTO volunteer.v_rainfall_events(
            datetime_record, title, status)
            VALUES ('{ datetime_record }', '{ title }', 'on');
    """
    try:
        do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
        status = get_recent_rainfalls()
        _data = status["data"][0]
        rainfall_event_id = _data["id"]
        status = get_rainfall_event_by_id(rainfall_event_id=rainfall_event_id)
        if status["status"]:
            status["detail"] = f"【成功創建豪雨事件】\n" + status["detail"]
        else:
            status["detail"] = f"無法創建豪雨事件-{ title } \n" + status["detail"]
        return status

    except Exception as e:
        return {"status": False, "detail": f"錯誤: { str(e) }"}
        