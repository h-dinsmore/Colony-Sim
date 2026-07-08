import pygame as pg

from mini_map import MiniMap
from info_ui import InfoUI

class UI:
    def __init__(self, cam, proc_gen, player, keyboard, chunk_renderer, weather, font, clock, village):
        self.mini_map = MiniMap(cam, proc_gen, player, keyboard, chunk_renderer, weather.sky.rgb)

        self.info_ui = InfoUI(self.mini_map, player, keyboard, weather, font, clock, village)

    def update(self, screen):
        self.mini_map.update(screen)
        self.info_ui.update(screen)