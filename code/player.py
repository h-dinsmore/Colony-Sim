import pygame as pg

class Player:
    def __init__(self, pos, spr_groups):
        super().__init__(spr_groups)
        self.pos = pos

        self.action = 'idle'
        self.facing_dir = 'left'
        self.inv = None
        