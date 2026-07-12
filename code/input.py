import pygame as pg

from settings import TILE_SIZE

class Keyboard:
    def __init__(self):
        self.held_keys = None
        self.pressed_keys = None

    def update(self):
        self.held_keys = pg.key.get_pressed()
        self.pressed_keys = pg.key.get_just_pressed()

class Mouse:
    def __init__(self, cam):
        self.cam = cam

        self.buttons_pressed = {'left': False, 'right': False}
        self.buttons_held = {'left': False, 'right': False}
    
    @property
    def screen_pos(self):
        return pg.Vector2(pg.mouse.get_pos())

    @property
    def world_pos(self):
        return (self.screen_pos / self.cam.zoom_scale) + self.cam.offset

    @property
    def tile_at(self):
        x, y = self.world_pos // TILE_SIZE
        return (int(x), int(y))
    
    @property
    def moving(self):
        return pg.mouse.get_rel() != (0, 0)
        
    def update(self):
        clicked = pg.mouse.get_just_pressed()
        self.buttons_pressed['left'] = clicked[0]
        self.buttons_pressed['right'] = clicked[2]

        held = pg.mouse.get_pressed()
        self.buttons_held['left'] = held[0]
        self.buttons_held['right'] = held[2]