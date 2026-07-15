import pygame as pg
import numpy as np

from villager import Villager
from settings import KEY_BINDINGS, MAP_TILE_SIZE, TILE_SIZE, SOLID_TILES, SURFACE_TERRAIN, FPS, Z_DIF_ICONS

class Player(Villager):
    def __init__(self, image, xyz, spr_groups, screen, keyboard, mouse, proc_gen, chunk_renderer):
        super().__init__(image, xyz, spr_groups, screen, proc_gen, chunk_renderer)
        self.keyboard = keyboard
        self.mouse = mouse
        self.player_spr, self.village_sprs = spr_groups

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
            z = int(self.proc_gen.z_map[new_x, new_y])

            if self.proc_gen.tile_map[new_x, new_y, z] != self.proc_gen.tile_ids['air'] and z <= self.z + 2:
                self.x, self.y = new_x, new_y
                self.rect.x += dx * TILE_SIZE
                self.rect.y += dy * TILE_SIZE
                
                if z < max(1, self.z - 1):
                    self.get_fall_damage(z) 

                if z != self.z:
                    for spr in [s for s in self.village_sprs if s not in self.player_spr]:
                        spr.update_visibility()

                    self.z = z
                    
                self.biome_in = self.proc_gen.id_biomes[int(self.proc_gen.biome_map[self.x, self.y])]

    def get_fall_damage(self, z):
        self.health = max(0, (self.z - z) * 2)
        if self.health <= 0:
            self.living = False
            self.kill()

    def check_removing_tile(self):
        if pg.mouse.get_pressed()[0]:
            x, y = self.mouse.tile_at
            z = int(self.proc_gen.z_map[x, y])
            if (tile_name := self.proc_gen.id_tiles[self.proc_gen.tile_map[x, y, z]]) in SOLID_TILES.keys() | SURFACE_TERRAIN:
                self.mine_tile(x, y, z)
            else:
                pass # chopping trees, gathering plants,
    
    def mine_tile(self, x, y, z):
        self.action = 'mining'
        hardness = max(0, self.proc_gen.tile_hardness_map[x, y, z] - ((self.strength * self.get_tool_strength()) / FPS))
        self.proc_gen.tile_hardness_map[x, y, z] = hardness
        if hardness == 0:
            self.proc_gen.tile_map[x, y, z] = self.proc_gen.tile_ids['air']
            self.proc_gen.z_map[x, y] = max(0, self.proc_gen.z_map[x, y] - 1)
            if z not in self.proc_gen.z_dif_map:
                self.proc_gen.update_z_dif_map(z)
            else:
                self.proc_gen.z_dif_map[z][x, y] = self.proc_gen.tile_ids['shallow valley']

            self.chunk_renderer.update_tile_in_chunk(x, y, z)

    def update(self):
        super().update()
        self.move()
        self.check_removing_tile()