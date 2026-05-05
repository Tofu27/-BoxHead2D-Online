import requests


def HttpPlayerCreator(username: str, base_url="http://localhost:8888") -> tuple:
    if not username.strip():
        return None, "用户名不能为空"
    try:
        response = requests.get(
            f"{base_url}/create",
            params={"name": username},
            timeout=5
        )
        result = response.json()
        if result.get("code") != 200:
            return None, result.get("error", "未知错误")
        return result["data"], None
    except requests.exceptions.RequestException as e:
        return None, f"网络错误: {e}"
    except ValueError:
        return None, "服务器响应格式错误"
    except Exception as e:
        return None, f"内部错误: {e}"