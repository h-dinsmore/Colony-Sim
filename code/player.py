import pygame as pg

from villager import Villager
from settings import KEY_BINDINGS, MAP_TILE_SIZE, TILE_SIZE

class Player(Villager):
    def __init__(self, image, xyz, spr_groups, screen, keyboard):
        super().__init__(image, xyz, spr_groups, screen)
        self.keyboard = keyboard

    def move(self):
        old_x, old_y = self.x, self.y

        if self.keyboard.pressed_keys[KEY_BINDINGS['+x']]:
            self.x = min(self.x + 1, MAP_TILE_SIZE[0] - 1)
        if self.keyboard.pressed_keys[KEY_BINDINGS['-x']]:
            self.x = max(self.x - 1, 0)

        if self.keyboard.pressed_keys[KEY_BINDINGS['+y']]:
            self.y = min(self.y + 1, MAP_TILE_SIZE[1] - 1)
        if self.keyboard.pressed_keys[KEY_BINDINGS['-y']]:
            self.y = max(self.y - 1, 0)

        self.rect.x += (self.x - old_x) * TILE_SIZE
        self.rect.y += (self.y - old_y) * TILE_SIZE

    def update(self):
        super().update()
        self.move()