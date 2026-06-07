import pygame as pg

from settings import MAP_SIZE, TILE_SIZE, RES

class Camera:
    def __init__(self, center_xy): 
        self.center_xy = center_xy

        self.offset = pg.Vector2()
        self.half_res = pg.Vector2(RES) / 2
        self.max_x, self.max_y = (pg.Vector2(MAP_SIZE[:2]) * TILE_SIZE) - self.half_res
        self.zoom_ratio, self.max_zoom_ratio, self.min_zoom_ratio = 1.0, 1.5, 0.5
        
    @property
    def tile_offset(self):
        return (self.offset + self.half_res) // TILE_SIZE

    def update(self, target_xy):
        target_dist = target_xy - self.center_xy
        if target_dist != 0.0:
            self.center_xy += (target_dist) 
            x, y = self.center_xy - self.half_res
            self.offset.x = max(0, min(x, int(self.max_x)))
            self.offset.y = max(0, min(y, int(self.max_y)))