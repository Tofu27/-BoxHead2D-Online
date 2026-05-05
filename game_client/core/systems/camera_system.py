from views.base_view import CAMERA_SPEED

class CameraSystem:
    """摄像机平滑跟随目标，并限制在地图边界内。"""
    def __init__(self, camera_sprites):
        self.camera = camera_sprites

    def follow(self, target, room_width, room_height, viewport_w, viewport_h):
        x = target.pos.x - viewport_w / 2
        y = target.pos.y - viewport_h / 2
        x = max(0, min(x, room_width - viewport_w))
        y = max(0, min(y, room_height - viewport_h))
        self.camera.move_to((x, y), CAMERA_SPEED)