import pygame as pg
import numpy as np

from villager import Villager
from settings import KEY_BINDINGS, MAP_TILE_SIZE, TILE_SIZE, TILE_REACH_RADIUS

class Player(Villager):
    def __init__(self, img_folder, xyz, spr_groups, screen, keyboard, mouse, proc_gen, chunk_renderer, village):
        super().__init__(img_folder, xyz, spr_groups, screen, proc_gen, chunk_renderer, village)
        self.keyboard = keyboard
        self.mouse = mouse
        self.player_spr, self.village_sprs = spr_groups

    def move(self):
        old_x, old_y = self.x, self.y
        new_x, new_y = old_x, old_y

        if (dx := self.keyboard.pressed_keys[KEY_BINDINGS['+x']] - self.keyboard.pressed_keys[KEY_BINDINGS['-x']]) != 0:
            new_x = max(0, min(self.x + dx, MAP_TILE_SIZE[0] - 1))

        if (dy := self.keyboard.pressed_keys[KEY_BINDINGS['+y']] - self.keyboard.pressed_keys[KEY_BINDINGS['-y']]) != 0:
            new_y = max(0, min(self.y + dy, MAP_TILE_SIZE[1] - 1))
        
        if new_x != old_x or new_y != old_y:
            z = int(self.proc_gen.z_map[new_x, new_y])

            if self.proc_gen.tile_map[new_x, new_y, z] != self.proc_gen.tile_ids['air'] and z <= self.z + TILE_REACH_RADIUS:
                self.x, self.y = new_x, new_y
                self.rect.x += dx * TILE_SIZE
                self.rect.y += dy * TILE_SIZE
                self.biome_in = self.proc_gen.id_biomes[int(self.proc_gen.biome_map[self.x, self.y])]

                if z < max(1, self.z - 1):
                    self.get_fall_damage(z) 

                if z != self.z:
                    for spr in [s for s in self.village_sprs if s not in self.player_spr]:
                        spr.update_visibility()

                    self.z = z
                    self.living = z > -1

    def check_removing_tile(self):
        if pg.mouse.get_pressed()[0]:
            x, y = self.mouse.tile_at
            z = self.z if self.chunk_renderer.view == 'z slice' else int(self.proc_gen.z_map[x, y])
            tile_name = self.proc_gen.id_tiles[self.proc_gen.tile_map[x, y, z]]
            if self.check_reachable_tile(x, y, z, tile_name == 'air'):
                self.remove_tile(x, y, z)

    def update(self):
        super().update()
        self.move()
        self.check_removing_tile()