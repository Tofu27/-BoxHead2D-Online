import requests

def HttpCreatePlayer(username):
    if not username:
        print("❌ 用户名不能为空！")
        return None, "用户名不能为空！"
    
    try:

        # 2. 请求 Golang HTTP 接口
        print(f"✅ 请求创建玩家：{username}")
        response = requests.get(
            url="http://localhost:8888/create",
            params={"name": username},
            timeout=5
        )

        # 3. 解析返回的 UUID
        result = response.json()
        print(result)
        if result["code"] != 200:
            print(f"❌ 创建失败：{result['error']}")
            return None, result["error"]

        print(f"✅ 获取玩家信息成功：{ result }")
        return result['data'], None

    except requests.exceptions.RequestException as err:
        print(f"❌ 网络请求失败：{err}")
        return None, f"网络错误：{err}"
    except ValueError as err:   # JSON 解析错误
        print(f"❌ 响应解析失败：{err}")
        return None, f"服务器响应格式错误"
    except Exception as err:
        print(f"❌ 未知错误：{err}")
        return None, f"内部错误：{err}"