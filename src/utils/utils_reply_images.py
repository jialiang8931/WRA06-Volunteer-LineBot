
from typing import List, Dict
from components import setting 
import datetime
import urllib.parse
from utils import create_squad_patrol_image_and_thumbnail



def get_squad_patrol_record_msg_or_img(target_squad_name):
    response_type = 'text'
    current_month_str = datetime.datetime.now().strftime("%Y-%m")
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month_str = (first - datetime.timedelta(days=1)).strftime("%Y-%m")
    records = create_squad_patrol_image_and_thumbnail.get_squad_patrol_record_by_name(target_squad_name, current_month_str, last_month_str)

    detail = {}
    if len(records) == 0:
        detail = {
            "msg": "無此分隊，請再確認。"
        }

    if len(records) != 0:
        response_type = "image"
        create_squad_patrol_image_and_thumbnail.create_patrol_record_image(target_squad_name, current_month_str, records)
        base_url = f"https://s3.ap-northeast-1.amazonaws.com/{ setting.org.lower() }.volunteer/images/statistics"
        squad_safe_string = urllib.parse.quote_plus(target_squad_name)
        original_content_url = f"{ base_url }/{ current_month_str }_{ squad_safe_string }.png"
        preview_image_url = f"{ base_url }/pre_{ current_month_str }_{ squad_safe_string }.png"
        detail = {
            "original_content_url": original_content_url,
            "preview_image_url": preview_image_url
        }

    return {
        "type": response_type,
        "detail": detail
    }
    