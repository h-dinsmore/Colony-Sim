import pygame as pg

from villager import Villager
from settings import KEY_BINDINGS, MAP_TILE_SIZE, TILE_SIZE

class Player(Villager):
    def __init__(self, image, xyz, spr_groups, screen, keyboard, proc_gen):
        super().__init__(image, xyz, spr_groups, screen, proc_gen)
        self.keyboard = keyboard

    def move(self):
        old_x, old_y = self.x, self.y
        new_x, new_y = old_x, old_y

        dx = self.keyboard.pressed_keys[KEY_BINDINGS['+x']] - self.keyboard.pressed_keys[KEY_BINDINGS['-x']]
        dy = self.keyboard.pressed_keys[KEY_BINDINGS['+y']] - self.keyboard.pressed_keys[KEY_BINDINGS['-y']]

        if dx != 0:
            new_x = max(0, min(self.x + dx, MAP_TILE_SIZE[0] - 1))

        if dy != 0:
            new_y = max(0, min(self.y + dy, MAP_TILE_SIZE[1] - 1))
        
        if new_x != old_x or new_y != old_y:
            z = self.proc_gen.z_map[new_x, new_y]
            if self.proc_gen.tile_map[new_x, new_y, z] != self.proc_gen.tile_ids['air'] and z <= self.z + 1:
                self.x, self.y = new_x, new_y
                self.rect.x += dx * TILE_SIZE
                self.rect.y += dy * TILE_SIZE
                if z < self.z - 1:
                    self.get_fall_damage(z)        
                self.z = z

    def get_fall_damage(self, z):
        self.health -= (self.z - z) * 2
        if self.health <= 0:
            self.living = False
            self.kill()

    def update(self):
        super().update()
        self.move()