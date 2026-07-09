import pygame as pg

from settings import MAP_PX_SIZE, TILE_SIZE, RES, KEY_BINDINGS

class Camera:
    def __init__(self, center_xy, keyboard): 
        self.center_xy = center_xy
        self.keyboard = keyboard
        
        self.offset = pg.Vector2(max(0, self.center_xy.x - RES[0]), max(0, self.center_xy.y - RES[1])) # topleft of the screen
        
        self.half_visible_world_px = pg.Vector2(RES) / 2
        self.max_centerx, self.max_centery = pg.Vector2(MAP_PX_SIZE[:2]) - self.half_visible_world_px
        
        self.zoom_scale, self.max_zoom_scale, self.min_zoom_scale = 1.0, 1.25, 0.75

    def update_zoom(self, dir):
        self.zoom_scale = max(self.min_zoom_scale, min(self.zoom_scale + (dir.y * 0.01), self.max_zoom_scale)) 
        self.half_visible_world_px = (pg.Vector2(RES) / 2) / self.zoom_scale
        self.max_centerx, self.max_centery = (pg.Vector2(MAP_PX_SIZE[:2]) - self.half_visible_world_px) 

    def update(self, target_xy):
        if (target_dist := target_xy - self.center_xy) != 0.0:
            self.center_xy.x = max(self.half_visible_world_px.x, min(target_xy.x, self.max_centerx))
            self.center_xy.y = max(self.half_visible_world_px.y, min(target_xy.y, self.max_centery))

            self.offset.x = max(0, min(
                self.center_xy.x - self.half_visible_world_px.x, 
                self.max_centerx - self.half_visible_world_px.x
            ))
            self.offset.y = max(0, min(
                self.center_xy.y - self.half_visible_world_px.y, 
                self.max_centery - self.half_visible_world_px.y
            ))

        if self.keyboard.pressed_keys[KEY_BINDINGS['reset zoom']]:
            self.zoom_scale = 1.0