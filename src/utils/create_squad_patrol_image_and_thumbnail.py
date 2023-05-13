from PIL import ImageDraw, ImageFont, Image
from PIL import ImageOps

import datetime
import os, io
import boto3
from components import setting
from utils import handler_routine_statistics

s3 = boto3.client('s3')

def get_squad_patrol_record_by_name(target_squad_name: str, current_month_str: str, last_month_str: str):
    res1 = handler_routine_statistics.get_routine_personal_patrol_record_by_month(month=last_month_str)
    res2 = handler_routine_statistics.get_routine_personal_patrol_record_by_month(month=current_month_str)
    
    records_last = list(filter(lambda x: x["squad"] == target_squad_name, res1))
    records_current = list(filter(lambda x: x["squad"] == target_squad_name, res2))
    records_last= sorted(records_last, key=lambda x: x["v_id"])
    records_current= sorted(records_current, key=lambda x: x["v_id"])

    def get_volunteer_metadata(volunteer):
        return {
            "v_id": volunteer["v_id"],
            "v_name" : volunteer["v_name"],
            "last_up": 0,
            "last_down": 0,
            "current_up": 0,
            "current_down": 0
        }
    # 2022-11-28 修正錯誤
    records = [get_volunteer_metadata(volunteer) for volunteer in (records_current if len(records_current) <= len(records_last) else records_last)]
    records = sorted(records, key=lambda x: x["v_id"])

    for i in range(0, len(records)):
        last_up = 1 if records_last[i]["first_half"] > 0 else 0
        last_down = 1 if records_last[i]["second_half"] > 0 else 0
        current_up = 1 if records_current[i]["first_half"] > 0 else 0
        current_down = 1 if records_current[i]["second_half"] > 0 else 0

        records[i] = {
            **records[i], 
            "last_up": last_up,
            "last_down": last_down,
            "current_up": current_up,
            "current_down": current_down
        }

    return records


def create_patrol_record_image(target_squad_name: str, 
                               current_month_str: str, 
                               records: list, 
                               based_dir: str = "images/statistics") -> None:
    try:
        people_count = len(records)
        row_spacing = 31
        img_width = 580
        img_height = 126 + row_spacing * people_count
        im = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 255)) 
        draw = ImageDraw.Draw(im)

        font_size = 16
        line_spacing = font_size
        font_path = os.path.join("/opt", 'volunteer_assets', 'assets', 'fonts', 'simsun.ttc')
        font = ImageFont.truetype(font_path, font_size)

        # 處理上下個月字串之部分
        current_month = datetime.datetime.now().strftime("%Y%m")
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = (first - datetime.timedelta(days=1)).strftime("%Y%m")

        columns = f'志工編號　　志工姓名　　{ last_month }上　　{ last_month }下　　{ current_month }上　　{ current_month }下'

        font_title = ImageFont.truetype(font_path, int(font_size * 2.4))
        img_title = target_squad_name
        draw.text((img_width//2 , line_spacing), img_title, anchor='mt', font=font_title, fill=(0, 0, 0, 255))
        draw.text((15, line_spacing * 3 + line_spacing * 0.75 * 2), columns, font=font, fill=(0, 0, 0, 255))


        for index_volunteer in range(0, people_count):
            offset_y = 0
            v_id = records[index_volunteer]["v_id"]
            v_name = records[index_volunteer]["v_name"]

            i = index_volunteer + 3
            record_position_y = line_spacing * (i+1) + line_spacing * 1 * i + offset_y
            draw.text((45, record_position_y ), v_id, anchor='mm', font=font, fill=(0, 0, 0, 255))
            draw.text((140, record_position_y), v_name, anchor='mm', font=font, fill=(0, 0, 0, 255))

            record = list(records[index_volunteer].values())[2:]
            record = list(map(str, record))
            record_spacing = 100
            for index_record in range(0, 4):
                text_color = (255, 255, 255, 255) if record[index_record] == "0" else (0, 0, 0, 255)
                bg_color = (124, 88, 200, 120) if record[index_record] == "0" else (107, 194, 53, 255)

                record_position_x = 230 + record_spacing * index_record
                rec_range_x = 20
                rec_range_y = 12
                rectangle_range = (record_position_x - rec_range_x, 
                                   record_position_y - rec_range_y, 
                                   record_position_x + rec_range_x,
                                   record_position_y + rec_range_y)
                draw.rectangle(rectangle_range, fill=bg_color)
                draw.text((record_position_x, record_position_y), record[index_record], anchor='mm', font=font, fill=text_color)
        output = io.BytesIO()
        im.save(output, format='png')
        img_bytes = output.getvalue()
        image_name = f'{ current_month_str }_{ img_title }.png'
        key = f"{ based_dir }/{ image_name }"
        with io.BytesIO(img_bytes) as img_file:
            s3.upload_fileobj(img_file, setting.bucket, key)
        
        # Create and upload thumbnail image
        thumbnail_name = f'pre_{ current_month_str }_{ img_title }.png'
        thumbnail_key = f"{ based_dir }/{ thumbnail_name }"
        
        thumbnail_size = (img_width//3, img_height//3)
        thumbnail_img = ImageOps.fit(im, thumbnail_size, method=Image.ANTIALIAS)
        output = io.BytesIO()
        thumbnail_img.save(output, format='png')
        img_bytes = output.getvalue()
        with io.BytesIO(img_bytes) as img_file:
            s3.upload_fileobj(img_file, setting.bucket, thumbnail_key)

        return 
    
    except Exception as e:
        print(e)
        return e
