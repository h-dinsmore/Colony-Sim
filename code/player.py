import pygame as pg
import numpy as np

from villager import Villager
from settings import KEY_BINDINGS, MAP_TILE_SIZE, TILE_SIZE, TILE_REACH_RADIUS, PLACEABLE_TILES, TILES_REMOVABLE_WITHOUT_PICKAXE, SURFACE_TERRAIN
from alarm import Alarm

class Player(Villager):
    def __init__(self, img_folder, xyz, spr_groups, screen, keyboard, mouse, proc_gen, chunk_renderer, village, assets, cam):
        super().__init__(img_folder, xyz, spr_groups, screen, proc_gen, chunk_renderer, village, assets, cam)
        self.keyboard = keyboard
        self.mouse = mouse
        self.player_spr, self.village_sprs = spr_groups

        self.is_player = True

        self.alarms = {'update tile remove check': Alarm(1000, self.update_tile_remove_check)} # pause for a second to avoid accidentally mining more tiles after
        self.tile_remove_check = True

    def move(self):
        dx, dy, xyz = self.get_movement_data()
        if (dx, dy) != (0, 0):
            self.x, self.y = xyz[:2]
            self.rect.move_ip(dx, dy)
            self.biome_in = self.proc_gen.id_biomes[int(self.proc_gen.biome_map[self.x, self.y])]
            if dx != 0:
                self.update_facing_dir(dx)

            z = xyz[2]
            if z != self.z:
                for spr in (s for s in self.village_sprs if s not in self.player_spr):
                    spr.update_visibility()

                if z < self.z - TILE_REACH_RADIUS:
                    self.get_fall_damage(z) 

                self.z = z
                self.living = z > -1

    def get_movement_data(self):
        x, y, z = self.x, self.y, self.z
        keys = self.keyboard.pressed_keys
        if (dx := keys[KEY_BINDINGS['+x']] - keys[KEY_BINDINGS['-x']]) != 0:
            x = max(0, min(self.x + dx, MAP_TILE_SIZE[0] - 1))
            dx *= TILE_SIZE
            
        if (dy := keys[KEY_BINDINGS['+y']] - keys[KEY_BINDINGS['-y']]) != 0:
            y = max(0, min(self.y + dy, MAP_TILE_SIZE[1] - 1))
            dy *= TILE_SIZE
        
        if x != self.x or y != self.y:
            z = int(self.proc_gen.z_map[x, y])

        if (x, y, z) != (self.x, self.y, self.z) and (self.proc_gen.tile_map[x, y, z] == self.proc_gen.tile_ids['air'] or \
            z > self.z + TILE_REACH_RADIUS):
            x, y, z = self.x, self.y, self.z

        return dx, dy, (x, y, z)

    def update_facing_dir(self, dx):
        if dx == TILE_SIZE and self.facing_dir == 'left': 
            self.facing_dir = 'right' 
            self.image = self.flipped_img

        elif dx == -TILE_SIZE and self.facing_dir == 'right':
            self.facing_dir = 'left'
            self.image = self.default_img

    def check_placing_tile(self):
        x, y = self.mouse.tile_at
        z = self.z if self.chunk_renderer.view == 'z slice' else int(self.proc_gen.z_map[x, y])
        if self.check_valid_tile(x, y, z):
            if self.item_holding in PLACEABLE_TILES and self.proc_gen.z_map[x, y] < MAP_TILE_SIZE[2] - 1 and \
                (int(self.proc_gen.surface_terrain_map[x, y]) == 0 or self.item_holding not in SURFACE_TERRAIN):
                    self.place_tile(x, y, z)

    def check_removing_tile(self):
        x, y = self.mouse.tile_at
        z = self.z if self.chunk_renderer.view == 'z slice' else int(self.proc_gen.z_map[x, y])
        if self.check_valid_tile(x, y, z):
            if self.item_holding is not None and 'pickaxe' in self.item_holding:
                self.remove_tile(x, y, z)
            else:
                if (surface_terrain_id := int(self.proc_gen.surface_terrain_map[x, y])) > 0:
                    tile_name = self.proc_gen.id_surface_terrain[surface_terrain_id]
                else:
                    tile_name = self.proc_gen.id_tiles[int(self.proc_gen.tile_map[x, y, z])]
                
                if tile_name in TILES_REMOVABLE_WITHOUT_PICKAXE:
                    self.remove_tile(x, y, z) 

    def update_tile_remove_check(self):
        self.tile_remove_check = True

    def update_item_holding(self):
        old_item = self.item_holding
        col, row = self.ui.player_inv_ui.col_row_overlap
        if (slot_num := (self.ui.player_inv_ui.num_cols * row) + col) < len(self.inv):
            self.item_holding = list(self.inv)[slot_num]
        else:
            self.item_holding = None

        if self.item_holding != old_item:
            self.update_item_holding_img()

    def update(self):
        super().update()
        self.move()
        
        if pg.mouse.get_just_pressed()[0]:
            self.check_placing_tile() if self.ui.player_inv_ui.col_row_overlap is None else self.update_item_holding()
        
        if self.tile_remove_check and pg.mouse.get_pressed()[2]:
            self.check_removing_tile()