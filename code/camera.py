import pygame as pg

from settings import MAP_PX_SIZE, TILE_SIZE, RES, KEY_BINDINGS

class Camera:
    def __init__(self, center_xy, keyboard): 
        self.center_xy = center_xy
        self.keyboard = keyboard

        self.offset = pg.Vector2()
        self.half_res = pg.Vector2(RES) / 2
        self.zoom_scale, self.max_zoom_scale, self.min_zoom_scale = 1.0, 1.25, 0.75
        
    @property
    def tile_offset(self):
        return (self.offset + self.half_res) // TILE_SIZE

    def update(self, target_xy):
        target_dist = target_xy - self.center_xy
        if target_dist != 0.0:
            self.center_xy += (target_dist) 
            x, y = self.center_xy - self.half_res
            self.offset.x = max(0, min(x, MAP_PX_SIZE[0] - round(RES[0] / self.zoom_scale)))
            self.offset.y = max(0, min(y, MAP_PX_SIZE[1] - round(RES[1] / self.zoom_scale)))

        if self.keyboard.pressed_keys[KEY_BINDINGS['reset zoom']]:
            self.zoom_scale = 1.0