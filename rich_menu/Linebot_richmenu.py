from PIL import Image, ImageFont, ImageDraw 
import requests
from json import loads, dumps
from io import BytesIO

#創建Richmenu
def create_richmenu(token, menu_json, menu_name):
    post_url = 'https://api.line.me/v2/bot/richmenu'
    r = requests.post(post_url, data = dumps(menu_json), headers = {"Authorization":"Bearer " + token, "Content-Type":"application/json"})
    if 'richMenuId' in loads(r.text).keys():
        print(menu_name + ' is now created!')
        return loads(r.text)['richMenuId']
    else: print('Create failed!\n' + r.text)

#上傳Richmenu的照片
def upload_richmenu_image(token, richmenu_id, image):
    post_url = 'https://api-data.line.me/v2/bot/richmenu/' + richmenu_id + '/content'
    r = requests.post(post_url, data = image, headers = {"Authorization":"Bearer " + token, "Content-Type":"image/png"})
    get_pic = requests.get(post_url, headers = {"Authorization":"Bearer " + token})
    if r.text == '{}': print('Image uploaded! Check now please!')
    else: print('Upload failed!\n' + r.text)
    return Image.open(BytesIO(get_pic.content))

#刪除Richmenu
def delete_richmenu(token, richmenu_id):
    post_url = 'https://api.line.me/v2/bot/richmenu/' + richmenu_id
    r = requests.delete(post_url, headers = {"Authorization":"Bearer " + token})
    if r.text == '{}': print('Richmenu is deleted!')
    else: print('Delete failed!\n' + r.text)

#設定為主畫面Richmenu
def set_default_richmenu(token, richmenu_id):
    post_url = 'https://api.line.me/v2/bot/user/all/richmenu/' + richmenu_id
    r = requests.post(post_url, headers = {"Authorization":"Bearer " + token})
    if r.text == '{}': print('Richmenu is now default!')
    else: print('Set default failed!\n' + r.text)

#取得所有Richmenu的列表，回傳為json
def get_richmenus(token):
    post_url = 'https://api.line.me/v2/bot/richmenu/list'
    r = requests.get(post_url, headers = {"Authorization":"Bearer " + token})
    return loads(r.text)

#刪除全部的Richmenus
def delete_all_richmenus(token):
    for each in get_richmenus(token)['richmenus']:
        print(each['name'] + ':' + each['richMenuId'])
        delete_richmenu(token, each['richMenuId'])