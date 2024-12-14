import requests
import time
import qrcode
import json
import os
import sys

def get_user_info(cookies):
    url = 'https://api.bilibili.com/x/web-interface/nav'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers, cookies=cookies)
    response.raise_for_status()
    data = response.json()
    if data['code'] == 0:
        user_info = data['data']
        return user_info
    else:
        print(f"获取用户信息失败，错误信息：{data['message']}")
        return None

def enable_auto_reply(cookies):
    SESSDATA = cookies.get("SESSDATA")
    bili_jct = cookies.get("bili_jct")

    url = "https://api.vc.bilibili.com/link_setting/v1/link_setting/set"
    data = {
        "keys_reply": "1",
        "csrf": bili_jct,
        "csrf_token": bili_jct
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.post(url, data=data, cookies=cookies, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            print("自动回复功能开启成功。")
        else:
            print(f"开启失败，错误信息：{result.get('message')}")
    else:
        print(f"请求失败，HTTP 状态码：{response.status_code}")

def get_qrcode():
    url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data['code'] == 0:
        qrcode_url = data['data']['url']
        qrcode_key = data['data']['qrcode_key']
        return qrcode_key, qrcode_url
    else:
        print(f"获取二维码失败，错误信息：{data['message']}")
        return None, None

def generate_qrcode(url):
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img.show()

def poll_login(qrcode_key):
    poll_url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'
    params = {
        'qrcode_key': qrcode_key
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    session = requests.Session()
    while True:
        response = session.get(poll_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        code = data['data']['code']
        if code == 0:
            print("登录成功！")
            cookies = session.cookies.get_dict()
            with open('bilibili_cookies.txt', 'w') as f:
                json.dump(cookies, f)
            return cookies
        elif code == 86101:
            print("二维码未扫码，请扫描二维码...")
            time.sleep(2)
        elif code == 86090:
            print("二维码已扫码未确认，请在手机客户端确认...")
            time.sleep(2)
        elif code == 86038:
            print("二维码已失效，请重新获取。")
            break
        else:
            print(f"发生错误：{data['data']['message']}")
            break
    return None

def display_user_info(cookies):
    user_info = get_user_info(cookies)
    if user_info and user_info.get('isLogin'):
        print("用户信息：")
        print(f"用户名: {user_info.get('uname', '未知用户')}")
        print(f"等级: {user_info.get('level_info', {}).get('current_level', '未知等级')}")
        print(f"硬币: {user_info.get('money', '未知')}")
        print(f"会员状态: {'是' if user_info.get('vipStatus') == 1 else '否'}")
        print(f"会员到期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user_info.get('vipDueDate') / 1000)) if user_info.get('vipDueDate') else '未知'}")
        return True
    else:
        print("Cookie 无效，请重新登录。")
        return False

def main():
    while True:
        if os.path.exists('bilibili_cookies.txt'):
            with open('bilibili_cookies.txt', 'r') as f:
                cookies = json.load(f)
            if display_user_info(cookies):
                choice = input("按回车键开启自动回复，输入 's' 切换账号...")
                if choice.lower() == 's':
                    os.remove('bilibili_cookies.txt')
                    print("请扫码登录...")
                    input("按回车键进行扫码登录...")
                    qrcode_key, qrcode_url = get_qrcode()
                    if qrcode_key:
                        generate_qrcode(qrcode_url)
                        cookies = poll_login(qrcode_key)
                        if cookies:
                            continue
                else:
                    enable_auto_reply(cookies)
                    break
            else:
                input("按回车键进行扫码登录...")
                qrcode_key, qrcode_url = get_qrcode()
                if qrcode_key:
                    generate_qrcode(qrcode_url)
                    cookies = poll_login(qrcode_key)
                    if cookies:
                        continue
        else:
            print("未检测到 Cookie 文件，请扫码登录。")
            input("按回车键进行扫码登录...")
            qrcode_key, qrcode_url = get_qrcode()
            if qrcode_key:
                generate_qrcode(qrcode_url)
                cookies = poll_login(qrcode_key)
                if cookies:
                    continue

if __name__ == '__main__':
    main()