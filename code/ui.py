import pygame as pg

from mini_map import MiniMap
from info_ui import InfoUI
from settings import TILE_SIZE, MAP_TILE_SIZE

class UI:
    def __init__(self, cam, proc_gen, player, keyboard, mouse, chunk_renderer, weather, assets, clock, village):
        self.mouse = mouse
        self.assets = assets
        self.chunk_renderer = chunk_renderer
        self.proc_gen = proc_gen
        self.cam = cam

        self.mini_map = MiniMap(cam, proc_gen, player, keyboard, chunk_renderer, weather.sky.sky_rgb)

        self.info_ui = InfoUI(self.mini_map, player, keyboard, weather, assets.fonts['default'], clock, village)

    def highlight_tile_at_mouse(self, screen):
        x, y = self.mouse.tile_at
        z = self.player.z if self.chunk_renderer.view == 'z slice' else int(self.proc_gen.z_map[x, y])

        tile_map = self.proc_gen.z_dif_map if self.chunk_renderer.view == 'elevation' else self.proc_gen.tile_map
        img = self.assets.get_img(self.chunk_renderer.get_img_path(tile_map[x, y, z])).copy()

        screen.blit(
            img if self.cam.zoom_scale == 1.0 else pg.transform.scale(img, pg.Vector2(TILE_SIZE, TILE_SIZE) * self.cam.zoom_scale), 
            (pg.Vector2(x, y) * TILE_SIZE) - self.cam.offset,
            special_flags=pg.BLEND_RGB_ADD
        )

    def update(self, screen):
        self.mini_map.update(screen)
        self.info_ui.update(screen)
        self.highlight_tile_at_mouse(screen)