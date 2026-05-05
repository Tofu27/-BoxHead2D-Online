from network.http import HttpPlayerCreator

class PlayerCreator:
    """处理通过 HTTP 创建玩家的业务逻辑，返回结构化结果。"""
    @staticmethod
    def create(username):
        info, err = HttpPlayerCreator(username)
        if err:
            return None, err
        return {"uuid": info["uuid"], "name": info["username"]}, None