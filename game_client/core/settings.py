class Setting:
    """Game settings."""

    def __init__(self,
                 e_volume: int,
                 m_volume: int,
                 r_idx: int,
                 fullscreen: bool,
                 lang_idx: int) -> None:
        self.effect_volume = e_volume
        self.music_volume = m_volume
        self.res_index = r_idx
        self.fullscreen = fullscreen
        self.lang_idx = lang_idx