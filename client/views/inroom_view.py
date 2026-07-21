# views/inroom_view.py
import arcade
import arcade.gui
from core.global_state import GlobalState, AppState
from core.proto import packets_pb2

class InRoomView(arcade.View):
    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self._setup_ui()

    def _setup_ui(self):
        self.room_info_label = arcade.gui.UITextArea(
            text="房间信息",
            width=400,
            height=40,
            font_size=18,
            text_color=arcade.color.BLACK,
        )
        self.player_list_box = arcade.gui.UIBoxLayout(vertical=True)

        self.leave_button = arcade.gui.UIFlatButton(text="退出房间", width=120)
        self.start_button = arcade.gui.UIFlatButton(text="开始游戏", width=120)

        hbox = arcade.gui.UIBoxLayout(vertical=False)
        hbox.add(self.leave_button.with_space_around(right=20))
        hbox.add(self.start_button.with_space_around(right=0))

        vbox = arcade.gui.UIBoxLayout()
        vbox.add(self.room_info_label.with_space_around(bottom=20))
        vbox.add(self.player_list_box.with_space_around(bottom=20))
        vbox.add(hbox)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x", anchor_y="center_y", child=vbox
            )
        )

        self.leave_button.on_click = self._on_leave_clicked
        self.start_button.on_click = self._on_start_clicked

    def on_show_view(self):
        if self.manager:
            self.manager.enable()

    def on_hide_view(self):
        if self.manager:
            self.manager.disable()

    def setup(self):
        """进入房间时刷新显示"""
        if self.manager:
            self.manager.enable()

        room = self.g.current_room
        if room:
            self.room_info_label.text = f"房间：{room.name} ({room.player_count}/{room.max_players})"
        else:
            self.room_info_label.text = "房间信息加载中...（等待服务器推送）"

        if self.g.room_players is None:
            self.g.room_players = []
        self._refresh_player_list()

    def _refresh_player_list(self):
        self.player_list_box.clear()
        players = self.g.room_players or []
        for user in players:
            label = arcade.gui.UITextArea(
                text=f"👤 {user.username}",
                width=200,
                height=25,
                font_size=14,
                text_color=arcade.color.BLACK,
            )
            self.player_list_box.add(label.with_space_around(bottom=5))

    # ===== 按钮事件 =====
    def _on_leave_clicked(self, event):
        """退出房间：发送离开请求，然后回到登录页"""
        # 发送离开房间请求
        pkt = packets_pb2.Packet()
        pkt.leave_room_request.SetInParent()
        self.g.ws.send(pkt)
        print("已发送离开房间请求")

        # 清理房间状态，切换到登录页
        self.g.current_room = None
        self.g.room_players = None
        self.g.switch_to(AppState.CONNECTED)

    def _on_start_clicked(self, event):
        """开始游戏请求"""
        pkt = packets_pb2.Packet()
        pkt.start_game_request.SetInParent()
        self.g.ws.send(pkt)
        print("已发送开始游戏请求")

    # ===== 网络消息处理 =====
    def on_update(self, delta_time):
        ws = self.g.ws
        if not ws:
            return
        pkt = ws.get_packet()
        if not pkt:
            return

        # 房间信息更新（玩家列表变化）
        if pkt.HasField('room_joined'):
            joined = pkt.room_joined
            self.g.current_room = joined.room
            self.g.room_players = joined.users
            self.room_info_label.text = f"房间：{joined.room.name} ({joined.room.player_count}/{joined.room.max_players})"
            self._refresh_player_list()

        # 处理拒绝响应
        elif pkt.HasField('deny_response'):
            reason = pkt.deny_response.reason
            print(f"房间内操作被拒绝：{reason}")
            # 如果被拒绝的原因是房间已销毁或玩家不在房间，可以自动跳转
            if "房间不存在" in reason or "不在房间" in reason:
                self.g.current_room = None
                self.g.room_players = None
                self.g.switch_to(AppState.CONNECTED)

        # 开始游戏成功（暂用 OkResponse 表示）
        elif pkt.HasField('ok_response'):
            print("开始游戏成功，即将切换至游戏对局（待实现）")
            # 后续可以切换至 INGAME 状态

    def on_draw(self):
        self.clear()
        self.manager.draw()