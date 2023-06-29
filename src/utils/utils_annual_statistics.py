from linebot.models import FlexSendMessage


def get_annual_statistic_flex_message(user_id):
    flex_message = FlexSendMessage(
        alt_text = "防汛志工年度通報統計",
        contents = {
          "type": "bubble",
          "size": "kilo",
          "direction": "ltr",
          "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "防汛志工年度通報統計",
                "size": "20px",
                "margin": "0px",
                "weight": "bold",
                "style": "normal",
                "decoration": "none",
                "align": "center",
                "gravity": "top",
              }
            ],
            "borderColor": "#0066FF"
          },
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "button",
                "action": {
                  "type": "uri",
                  "label": "民國112年 西元2023年",
                  "uri": "https://liff.line.me/2000002087-w65yOOAG/?year=2023",
                  "altUri": {
                    "desktop": "https://www.google.com/maps"
                  }
                },
                "height": "sm",
                "style": "primary",
                "gravity": "top",
                "margin": "0px",
                "adjustMode": "shrink-to-fit",
                "color": "#5500DD8D"
              },
              {
                "type": "button",
                "action": {
                  "type": "uri",
                  "label": "民國113年 西元2024年",
                  "uri": "https://liff.line.me/2000002087-w65yOOAG/?year=2024",
                  "altUri": {
                    "desktop": "https://www.google.com/maps"
                  }
                },
                "style": "primary",
                "height": "sm",
                "margin": "10px",
                "color": "#5500DD8D"
              }
            ],
            "position": "relative",
            "margin": "0px"
          },
          "styles": {
            "header": {
              "backgroundColor": "#0088008F",
            }
          }
        }
    )
    return flex_message
