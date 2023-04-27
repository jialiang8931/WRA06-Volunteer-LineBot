from components.do_transaction_pg import do_transaction_command_manage, get_dict_data_from_database
from components import line_bot_api
from components import setting 


def get_user_infos():
    sql_string = f"""
        SELECT group_id, user_id FROM volunteer.v_ingroup;
    """
    user_infos = get_dict_data_from_database(config_db=setting.config_db, sql_string=sql_string)
    return user_infos

def get_user_profile(user_info):
    response = line_bot_api.get_group_member_profile(user_info["group_id"], user_info["user_id"])
    response.picture_url = response.picture_url if response.picture_url != None else "https://cdn-icons-png.flaticon.com/512/9131/9131529.png"
    result = {**user_info, "display_name": response.display_name, "picture_url": response.picture_url}
    return result

def generate_update_user_info_string(new_user_info):
    sql_string = f"""UPDATE volunteer.v_ingroup SET display_name = '{ new_user_info["display_name"] }', picture_url = '{ new_user_info["picture_url"] }' WHERE user_id = '{ new_user_info["user_id"] }' AND group_id = '{ new_user_info["group_id"] }';\n"""
    return sql_string
    
def update_user_info():
    user_infos = get_user_infos()
    sql_string = ""
    for user_info in user_infos:
        try:
            new_user_info = get_user_profile(user_info)
            _sql_string = generate_update_user_info_string(new_user_info)
            sql_string += _sql_string
        except Exception as e:
            pass
    do_transaction_command_manage(config_db=setting.config_db, sql_string=sql_string)
    return {
        "status": True,
        "msg": "已更新所有使用者的 Profile"
    }