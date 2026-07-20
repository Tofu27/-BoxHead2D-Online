# views/inhall_view.py
import arcade
import arcade.gui
from core.global_state import GlobalState, AppState
from core.proto import packets_pb2

class InHallView(arcade.View):
    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.room_list = []   # 存储 RoomInfo 对象
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self._setup_ui()

    def _setup_ui(self):
        # 创建 UI 组件
        self.refresh_button = arcade.gui.UIFlatButton(text="刷新", width=120)
        self.create_button = arcade.gui.UIFlatButton(text="创建房间", width=120)
        self.join_button = arcade.gui.UIFlatButton(text="加入房间", width=120)
        self.room_list_box = arcade.gui.UIBoxLayout(vertical=True)

        # 布局（简化）
        hbox = arcade.gui.UIBoxLayout(vertical=False)
        hbox.add(self.refresh_button.with_space_around(right=10))
        hbox.add(self.create_button.with_space_around(right=10))
        hbox.add(self.join_button.with_space_around(right=10))

        vbox = arcade.gui.UIBoxLayout()
        vbox.add(hbox.with_space_around(bottom=20))
        vbox.add(self.room_list_box)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x", anchor_y="center_y", child=vbox
            )
        )

        # 绑定事件
        self.refresh_button.on_click = self._on_refresh_clicked
        self.create_button.on_click = self._on_create_clicked
        self.join_button.on_click = self._on_join_clicked

    def setup(self):
        """进入大厅时发送房间列表请求"""
        print("InHallView: 请求房间列表")
        print(f"当前用户ID: { self.g.user_id }")
        self._send_room_list_request()

    def _send_room_list_request(self):
        pkt = packets_pb2.Packet()
        pkt.room_list_request.SetInParent()
        self.g.ws.send(pkt)

    def _on_refresh_clicked(self, event):
        self._send_room_list_request()

    def _on_create_clicked(self, event):
        # 可弹出对话框输入房间名和最大人数，这里简化
        pkt = packets_pb2.Packet()
        req = pkt.create_room_request
        req.name = "MyRoom"
        req.max_players = 4
        self.g.ws.send(pkt)

    def _on_join_clicked(self, event):
        # 可点击列表项选择，简化：加入第一个房间
        if self.room_list:
            pkt = packets_pb2.Packet()
            req = pkt.join_room_request
            req.room_id = self.room_list[0].room_id
            self.g.ws.send(pkt)

    def on_update(self, delta_time):
        ws = self.g.ws
        if ws:
            pkt = ws.get_packet()
            if pkt:
                if pkt.HasField('room_list_response'):
                    self._update_room_list(pkt.room_list_response.rooms)
                elif pkt.HasField('room_list_update'):
                    self._apply_room_update(pkt.room_list_update)
                elif pkt.HasField('room_joined'):
                    # 成功加入房间，切换到 InGame 状态
                    print(f"加入房间成功：{pkt.room_joined.room.name}")
                    self.g.switch_to(AppState.INGAME)

    def _update_room_list(self, rooms):
        self.room_list = list(rooms)
        self._refresh_ui_list()

    def _apply_room_update(self, update):
        # 增量更新
        for added in update.added:
            self.room_list.append(added)
        for removed_id in update.removed:
            self.room_list = [r for r in self.room_list if r.room_id != removed_id]
        self._refresh_ui_list()

    def _refresh_ui_list(self):
        # 清空并重建列表显示
        self.room_list_box.clear()
        for room in self.room_list:
            label = arcade.gui.UITextArea(
                text=f"{room.name} ({room.player_count}/{room.max_players}) 房主:{room.host_name}",
                width=300,
                height=30,
                font_size=14,
                text_color=arcade.color.BLACK,
            )
            # 点击条目可加入房间
            # 可添加按钮或点击事件，此处简化
            self.room_list_box.add(label.with_space_around(bottom=5))

    def on_draw(self):
        self.clear()
        self.manager.draw()