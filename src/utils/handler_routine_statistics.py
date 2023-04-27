import datetime
from typing import List, Dict
from utils import do_transaction_pg
from constants import setting 
from functools import reduce


def get_routine_personal_patrol_record_by_month(org: str = setting.org, month: str = "2023-02") -> List[Dict]:
    year = month.split("-")[0]
    month_begin = datetime.datetime.strptime(month, "%Y-%m")
    month_begin_string = month_begin.strftime("%Y-%m-%d")
    is_February = month_begin.month == 2

    def __get_event_list_by_month(month_begin_string: str) -> list:
        sql_string = f"""
            SELECT id
                , TO_CHAR(datetime_begin, 'YYYY-MM-DD HH24:MI:SS') AS begin
                , TO_CHAR(datetime_end, 'YYYY-MM-DD HH24:MI:SS') AS end
            FROM volunteer.v_rainfall_events
            WHERE datetime_begin BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
            ORDER BY id
        """
        data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        return data

    # 取得當月豪雨事件列表
    rainfall_events = __get_event_list_by_month(month_begin_string)
    event_sql_strings = [
        f"""AND datetime NOT BETWEEN timestamp '{ event['begin'] }' AND timestamp '{ event['end'] }'"""
        for event in rainfall_events
    ]
    event_sql_string = '\n'.join(event_sql_strings)

    # 處理二月分統計之部分
    h2_sql_string = """EXTRACT(DAY FROM date) >= 16 AND EXTRACT(DAY FROM date) <= 30"""
    # if is_February:
    #     h2_sql_string = f"""EXTRACT(DAY FROM date) >= EXTRACT(DAY FROM DATE '{ month_begin_string }' + INTERVAL '1' MONTH - INTERVAL '1' DAY) - 4 AND EXTRACT(DAY FROM date) <= EXTRACT(DAY FROM DATE '{ month_begin_string }' + INTERVAL '1' MONTH - INTERVAL '1' DAY)"""

    # 取得當月日常通報統計
    sql_string = f"""
        WITH 
            v_list AS (
                SELECT ingroup.user_id
                    , v_list.v_id
                    , v_list.v_name
                    , v_list.basin_name
                    , v_list.region
                    , v_list.squad
                    , v_list.patrol_area_name
                    , v_list.note
                    , v_list.member
                    , v_list.couple_group
                FROM volunteer.v_list AS v_list 
                LEFT JOIN volunteer.v_ingroup AS ingroup ON ingroup.v_id = v_list.v_id
                WHERE v_list.org = '{ org }' AND year = { year }
                ORDER BY v_id ASC
            ),

            ori_msgs AS (
                SELECT * FROM volunteer.v_msgs
                WHERE datetime BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
                    AND msg_type IN ('image', 'video')
                    { event_sql_string }
            ),

            ori_update_record AS (
                SELECT * FROM volunteer.v_msgs
                WHERE msg_type = 'update'
                    AND date BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
                    { event_sql_string }
            ),
            update_record_h1 AS (
                SELECT group_id, user_id, 1 AS count FROM ori_update_record
                WHERE content = '1'
                    AND EXTRACT(DAY FROM date) <= 15
                    AND datetime IN(
                        SELECT MAX(datetime) FROM ori_update_record 
                        GROUP BY group_id, user_id, EXTRACT(YEAR FROM datetime), date
                    )
            ),
            update_record_h2 AS (
                SELECT group_id, user_id, 1 AS count FROM ori_update_record
                WHERE content = '1'
                    AND { h2_sql_string }
                    AND datetime IN(
                        SELECT MAX(datetime) FROM ori_update_record 
                        GROUP BY group_id, user_id, EXTRACT(YEAR FROM datetime), date
                    )
            ),

            ori_msg_stat_h1 AS (
                SELECT group_id, user_id, COUNT(*)/COUNT(*) AS count FROM ori_msgs
                WHERE EXTRACT(DAY FROM datetime) >= 1 AND EXTRACT(DAY FROM datetime) <= 15
                GROUP BY group_id, user_id
            ),

            ori_msg_stat_h2 AS (
                SELECT group_id, user_id, COUNT(*)/COUNT(*) AS count FROM ori_msgs
                WHERE { h2_sql_string }
                GROUP BY group_id, user_id
            ),

            stat_h1 AS (
                SELECT * FROM ori_msg_stat_h1
                UNION (SELECT * FROM update_record_h1)
            ),

            stat_h2 AS (
                SELECT * FROM ori_msg_stat_h2
                UNION (SELECT * FROM update_record_h2)
            ),

            output_data AS (
                SELECT v_list.v_id
                    , v_list.user_id
                    , v_list.v_name
                    , v_list.basin_name
                    , v_list.region
                    , v_list.squad
                    , v_list.patrol_area_name
                    , v_list.note
                    , v_list.member
                    , v_list.couple_group
                    , COALESCE(stat_h1.count, 0) AS h1
                    , COALESCE(stat_h2.count, 0) AS h2
                FROM v_list
                LEFT JOIN stat_h1 ON v_list.user_id = stat_h1.user_id
                LEFT JOIN stat_h2 ON v_list.user_id = stat_h2.user_id
                ORDER BY v_list.v_id
            )

        SELECT * FROM output_data;
    """
    
    #原始統計(包含原始通報、承辦更新、排除事件開立時段)
    data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)

    # 處理夫妻共同巡檢資料
    is_couple = list(filter(lambda x: x['couple_group'] != None, data))
    not_couple = list(filter(lambda x: x['couple_group'] == None, data))

    for couple in is_couple:
        couple_group = couple['couple_group']
        target_couple = list(filter(lambda x: x['couple_group'] == couple_group, is_couple))
        max_first_half = 0
        max_second_half = 0
        for _couple in target_couple:
            first_half = _couple['h1']
            second_half = _couple['h2']
            max_first_half = first_half if first_half >  max_first_half else max_first_half
            max_second_half = second_half if second_half >  max_second_half else max_second_half
        for _couple in target_couple:
            _couple['h1'] = max_first_half
            _couple['h2'] = max_second_half
        
    data = [*is_couple, *not_couple]
    data = [{
        "basin_name": x['basin_name'],
        "squad": x["squad"],
        "region": x["region"],
        "patrol_area_name": x["patrol_area_name"],
        "v_id": x["v_id"],
        "v_name": x["v_name"],
        "first_half": 1 if x["h1"] >= 1 else 0,
        "second_half": 1 if x["h2"] >= 1 else 0,
    } for x in data]    
    return data


def get_routine_regional_patrol_record_by_month(org: str = setting.org, month: str = "2023-01") -> List[Dict]:
    year = month.split("-")[0]
    month_begin = datetime.datetime.strptime(month, "%Y-%m")
    month_begin_string = month_begin.strftime("%Y-%m-%d")
    is_February = month_begin.month == 2

    def __get_event_list_by_month(month_begin_string: str) -> list:
        sql_string = f"""
            SELECT id
                , TO_CHAR(datetime_begin, 'YYYY-MM-DD HH24:MI:SS') AS begin
                , TO_CHAR(datetime_end, 'YYYY-MM-DD HH24:MI:SS') AS end
            FROM volunteer.v_rainfall_events
            WHERE datetime_begin BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
            ORDER BY id
        """
        data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
        return data

    # 取得當月豪雨事件列表
    rainfall_events = __get_event_list_by_month(month_begin_string)
    event_sql_strings = [
        f"""AND datetime NOT BETWEEN timestamp '{ event['begin'] }' AND timestamp '{ event['end'] }'"""
        for event in rainfall_events
    ]
    event_sql_string = '\n'.join(event_sql_strings)

    # 處理二月分統計之部分
    h2_sql_string = """EXTRACT(DAY FROM date) >= 16 AND EXTRACT(DAY FROM date) <= 30"""
    # if is_February:
    #     h2_sql_string = f"""EXTRACT(DAY FROM date) >= EXTRACT(DAY FROM DATE '{ month_begin_string }' + INTERVAL '1' MONTH - INTERVAL '1' DAY) - 4 AND EXTRACT(DAY FROM date) <= EXTRACT(DAY FROM DATE '{ month_begin_string }' + INTERVAL '1' MONTH - INTERVAL '1' DAY)"""

    # 取得當月日常通報統計
    sql_string = f"""
        WITH 
            v_list AS (
                SELECT ingroup.user_id
                    , v_list.v_id
                    , v_list.v_name
                    , v_list.basin_name
                    , v_list.region
                    , v_list.squad
                    , v_list.patrol_area_name
                    , v_list.note
                    , v_list.member
                    , v_list.couple_group
                FROM volunteer.v_list AS v_list 
                LEFT JOIN volunteer.v_ingroup AS ingroup ON ingroup.v_id = v_list.v_id
                WHERE v_list.org = '{ org }' AND year = { year }
                ORDER BY v_id ASC
            ),

            ori_msgs AS (
                SELECT * FROM volunteer.v_msgs
                WHERE datetime BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
                    AND msg_type IN ('image', 'video')
                    { event_sql_string }
            ),

            ori_update_record AS (
                SELECT * FROM volunteer.v_msgs
                WHERE msg_type = 'update'
                    AND date BETWEEN DATE '{ month_begin_string }' AND DATE '{ month_begin_string }' + INTERVAL '1' MONTH 
                    { event_sql_string }
            ),
            update_record_h1 AS (
                SELECT group_id, user_id, 1 AS count FROM ori_update_record
                WHERE content = '1'
                    AND EXTRACT(DAY FROM date) <= 15
                    AND datetime IN(
                        SELECT MAX(datetime) FROM ori_update_record 
                        GROUP BY group_id, user_id, EXTRACT(YEAR FROM datetime), date
                    )
            ),
            update_record_h2 AS (
                SELECT group_id, user_id, 1 AS count FROM ori_update_record
                WHERE content = '1'
                    AND { h2_sql_string }
                    AND datetime IN(
                        SELECT MAX(datetime) FROM ori_update_record 
                        GROUP BY group_id, user_id, EXTRACT(YEAR FROM datetime), date
                    )
            ),

            ori_msg_stat_h1 AS (
                SELECT group_id, user_id, COUNT(*)/COUNT(*) AS count FROM ori_msgs
                WHERE EXTRACT(DAY FROM datetime) >= 1 AND EXTRACT(DAY FROM datetime) <= 15
                GROUP BY group_id, user_id
            ),

            ori_msg_stat_h2 AS (
                SELECT group_id, user_id, COUNT(*)/COUNT(*) AS count FROM ori_msgs
                WHERE { h2_sql_string }
                GROUP BY group_id, user_id
            ),

            stat_h1 AS (
                SELECT * FROM ori_msg_stat_h1
                UNION (SELECT * FROM update_record_h1)
            ),

            stat_h2 AS (
                SELECT * FROM ori_msg_stat_h2
                UNION (SELECT * FROM update_record_h2)
            ),

            output_data AS (
                SELECT v_list.v_id
                    , v_list.user_id
                    , v_list.v_name
                    , v_list.basin_name
                    , v_list.region
                    , v_list.squad
                    , v_list.patrol_area_name
                    , v_list.note
                    , v_list.member
                    , v_list.couple_group
                    , COALESCE(stat_h1.count, 0) AS h1
                    , COALESCE(stat_h2.count, 0) AS h2
                FROM v_list
                LEFT JOIN stat_h1 ON v_list.user_id = stat_h1.user_id
                LEFT JOIN stat_h2 ON v_list.user_id = stat_h2.user_id
                ORDER BY v_list.v_id
            )

        SELECT 
            basin_name, region, patrol_area_name, SUM(h1) h1, SUM(h2) h2
        FROM output_data
        GROUP BY basin_name, region, patrol_area_name
        ;
    """
    
    #原始統計(包含原始通報、承辦更新、排除事件開立時段)
    data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    return data

def get_personal_recent_2month_record(user_id = 'U92dd2242c916770f89c413845311bbe2'):

    # 生成豪雨事件開設排除清單
    sql_string = f"""
        SELECT datetime_begin::VARCHAR, datetime_end::VARCHAR
        FROM volunteer.v_rainfall_events
        WHERE datetime_begin > (CURRENT_DATE - INTERVAL '2 MONTH')
        ;
    """
    data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    sub_sql = ""
    for event in data:
        sub_sql += f"""\nAND NOT (datetime BETWEEN timestamp '{ event["datetime_begin"] }' AND timestamp '{ event["datetime_end"] }')"""

    sql_string = f'''
        WITH 
            msgs AS (
                SELECT * FROM volunteer.v_msgs 
                WHERE msg_type = 'image'
                    AND datetime > CURRENT_DATE - INTERVAL '2 MONTH'
                    AND user_id = '{ user_id }' 
                    { sub_sql }
            )
        SELECT 'last_first' _session, COALESCE(SUM(records.last_first), 0)::INT AS records FROM ( 
            SELECT count(date) as last_first FROM msgs
            WHERE date BETWEEN DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '10 DAY' AND 
                            DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '15 day'
            GROUP BY date 
        ) records 

        UNION
        SELECT 'last_second' _session, COALESCE(SUM(records.last_second), 0)::INT AS records FROM ( 
            SELECT count(date) as last_second FROM msgs
            WHERE date BETWEEN DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '24 day' AND 
                            DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '31 day'
            GROUP BY date 
        ) records

        UNION
        SELECT 'current_first' _session, COALESCE(SUM(records.current_first), 0)::INT AS records FROM ( 
            SELECT count(date) as current_first FROM msgs
            WHERE date BETWEEN DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '10 DAY' AND 
                            DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '15 day'
            GROUP BY date 
        ) records 

        UNION
        SELECT 'current_second' _session, COALESCE(SUM(records.current_second), 0)::INT AS records FROM ( 
            SELECT count(date) as current_second FROM msgs
            WHERE date BETWEEN DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '24 DAY' AND 
                            DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '31 day'
            GROUP BY date 
        ) records 

        ORDER BY _session DESC;
    '''

    update_sql_string = f'''
        (SELECT 'last_first' _session, MAX(datetime), content::INT AS records FROM ( 
            SELECT datetime, content FROM volunteer.v_msgs 
            WHERE user_id = '{ user_id }'
                AND date BETWEEN DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AND 
                            DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '14 day'
                AND msg_type = 'update'
        ) records 
        GROUP BY datetime, content)

        UNION (
        SELECT 'last_second' _session, MAX(datetime), content::INT AS records FROM ( 
            SELECT datetime, content FROM volunteer.v_msgs 
            WHERE user_id = '{ user_id }'
                AND date BETWEEN DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '15 day' AND 
                            DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 day'
                AND msg_type = 'update'
        ) records 
        GROUP BY datetime, content)

        UNION (
        SELECT 'current_first' _session, MAX(datetime), content::INT AS records FROM ( 
            SELECT datetime, content FROM volunteer.v_msgs 
            WHERE user_id = '{ user_id }'
                AND date BETWEEN DATE_TRUNC('month', CURRENT_DATE) AND 
                            DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '14 day'
                AND msg_type = 'update'
        ) records 
        GROUP BY datetime, content )

        UNION (
        SELECT 'current_second' _session, MAX(datetime), content::INT AS records FROM ( 
            SELECT datetime, content FROM volunteer.v_msgs 
            WHERE user_id = '{ user_id }'
                AND date BETWEEN DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '15 day' AND 
                            DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day'
                AND msg_type = 'update'
        ) records 
        GROUP BY datetime, content)
    '''

    data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    data = [data[1], data[0], data[3], data[2]]
    data = list(map(lambda x: 4 if x['records'] > 0 else 0, data))

    try: # 這部分處理承辦修改的部分
        updated_data = do_transaction_pg.get_dict_data_from_database(config_db=setting.config_db, sql_string=update_sql_string)
        for _data in updated_data:
            session = _data['_session']
            value = 4 if _data['records'] == 1 else 0
            index_data = ['last_first', 'last_second', 'current_first', 'current_second'].index(session)
            data[index_data] = value
    except Exception as e:
        pass

    current_month = datetime.datetime.now().strftime("%Y-%m")
    previous_month = (datetime.datetime.now() - datetime.timedelta(days = datetime.datetime.now().day + 1)).strftime("%Y-%m")
    
    data = [
        {"month": previous_month, "first": data[0], 'second': data[1]},
        {"month": current_month, "first": data[2], 'second': data[3]}
    ]
    
    tmp = reduce(lambda x, record: f"{x}\n{record['month']}\n => 上旬{str(record['first'])}，下旬{str(record['second'])}，共{ str(record['first'] + record['second']) }小時", data, f'{ "近兩個月通報時數統計" }')

    return tmp