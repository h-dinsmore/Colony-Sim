import pygame as pg
from random import randint, choice

from settings import MONTHS_DAYS, TILE_SIZE, TILE_REACH_RADIUS, TREES, FPS, SURFACE_TERRAIN, LIQUIDS, SOLID_TILES

class Villager(pg.sprite.Sprite):
    def __init__(self, img_folder, xyz, spr_groups, screen, proc_gen, chunk_renderer, village, assets, cam):
        super().__init__(*spr_groups)
        self.img_folder = img_folder
        self.action = 'idle'
        self.image = img_folder[self.action]
        self.image.set_colorkey((0, 0, 0))
        self.x, self.y, self.z = xyz
        self.rect = self.image.get_rect(center=(pg.Vector2(self.x, self.y) * TILE_SIZE))
        self.screen = screen
        self.proc_gen = proc_gen
        self.chunk_renderer = chunk_renderer
        self.village = village
        self.assets = assets
        self.cam = cam
        self.ui = None # not initialized yet

        self.facing_dir = 'left'
        self.default_img = self.image.copy()
        self.flipped_img = pg.transform.flip(self.image, True, False)
        self.visible = True
        self.biome_in = proc_gen.id_biomes[int(proc_gen.biome_map[self.x, self.y])]
        self.alarms = {}

        self.inv = {}
        self.num_inv_slots = 64
        self.max_slot_storage = 64
        self.item_holding, self.item_holding_img = None, None
        self.item_holding_bg = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
        self.item_holding_bg.fill((255, 255, 255))
        
        self.hunger = 100 
        self.thirst = 100
        self.sleep = 100
        self.mood = 100
        self.health = 100
        self.strength = 100
        self.living = True

        self.relations = {
            'family': {},
            'friends': {},
            'enemies': {},
            'partner': None
        }
        self.age = randint(18, 36)
        birth_month = choice(list(MONTHS_DAYS.keys()))
        self.birthday = f'{birth_month} {randint(0, MONTHS_DAYS[birth_month])}'
        self.strengths = {}
        self.weaknesses = {}
        self.hobbies = {}
        self.memories = {}
        self.fears = {}

        self.is_player = False

    def update_visibility(self, player):
        px, py = player.rect.center
        x, y = self.rect.center
        z_map = self.proc_gen.z_map
        self.visible = abs(px - x) < RES[0] // 2 and abs(py - y) < RES[1] // 2 and z_map[x, y] <= z_map[px, py]

    def get_fall_damage(self, z):
        self.health = max(0, (self.z - z) * 2)
        if self.health <= 0:
            self.living = False
            self.kill()

    def check_valid_tile(self, x, y, z):
        return (self.proc_gen.surface_terrain_map[x, y] > 0 or self.proc_gen.tile_map[x, y, z] != self.proc_gen.tile_ids['air']) and \
            abs(self.x - x) <= TILE_REACH_RADIUS and abs(self.y - y) <= TILE_REACH_RADIUS and \
            ((abs(self.z - z) <= TILE_REACH_RADIUS) if self.chunk_renderer.view != 'z slice' else z == self.proc_gen.z_map[x, y])
           
    def remove_tile(self, x, y, z):
        if (name := self.chunk_renderer.get_tile_name(x, y)) in SURFACE_TERRAIN:
            hardness_map = self.proc_gen.surface_terrain_hardness_map
            idx = (x, y) 
        else:
            hardness_map = self.proc_gen.tile_hardness_map
            idx = (x, y, z)
        
        if hardness_map[idx] > 0:
            hardness_map[idx] -= min(hardness_map[idx], int((self.strength * self.get_tool_strength()) / FPS))

        if hardness_map[idx] == 0:
            self.update_inv(name, add=True)
            self.proc_gen.update_maps_after_removed_tile(x, y, z, name) # update the tile map before the chunk renderer to show the tile below
            name = self.chunk_renderer.get_tile_name(x, y)
            self.ui.mini_map.update_tile_in_chunk(x, y, z, name) # only updating after a removed tile bc it doesn't render alphas like the chunk renderer
            
            if (new_z := int(self.proc_gen.z_map[x, y])) < z:
                if (x, y) == (self.x, self.y):
                    self.z = new_z
                    self.living = new_z > -1

                if z in self.proc_gen.z_dif_map:
                    self.proc_gen.update_z_dif_map_tile(x, y, z, new_z)

                self.ui.mini_map.update_chunk_img_cache_key(x, y, z, new_z)
                self.chunk_renderer.update_chunk_img_cache_key(x, y, z, new_z)

            if self.is_player:
                self.tile_remove_check = False
                self.alarms['update tile remove check'].start()
        
        self.chunk_renderer.update_tile_in_chunk(x, y, name, hardness_map[idx])

    def get_tool_strength(self):
        if self.item_holding is None:
            return 1
        
        return 10

    def update_inv(self, item_name, add=False, remove=False):
        if item_name in TREES:
            item_name = 'wood'

        item_amount = (1 if item_name != 'wood' else 4)
        if add:
            self.add_inv_item(item_name, item_amount)
        else:
            self.remove_inv_item(item_name, item_amount)

    def add_inv_item(self, name, amount):
        if f'{name} 0' not in self.inv:
            if len(self.inv) < self.num_inv_slots:
                self.inv[f'{name} 0'] = {'amount': amount, 'idx': len(self.inv)}
        else:
            num_slots_with_item = len([k for k in self.inv if name in k])
            current_slot = self.inv[f'{name} {num_slots_with_item - 1}']
            if (new_slot_amount := (current_slot['amount'] + amount)) <= self.max_slot_storage:
                current_slot['amount'] = new_slot_amount
            
            elif len(self.inv) < self.num_inv_slots:
                current_slot['amount'] = self.max_slot_storage
                self.inv[f'{name} {num_slots_with_item}'] = {'amount': new_slot_amount - self.max_slot_storage, 'idx': num_slots_with_item}

    def remove_inv_item(self, name, amount):
        num_slots_with_item = len([k for k in self.inv if name in k])
        slot = self.inv[f'{name} {num_slots_with_item - 1}']
        slot['amount'] -= amount
        if slot['amount'] == 0:
            idx = slot['idx']
            del self.inv[f'{name} {num_slots_with_item - 1}']
            if num_slots_with_item == 1:
                self.item_holding = None

            for slot_k in [k for k in self.inv if self.inv[k]['idx'] > idx]:
                self.inv[slot_k]['idx'] -= 1

    def place_tile(self, x, y, z):
        if self.item_holding in SURFACE_TERRAIN:
            self.proc_gen.surface_terrain_map[x, y] = self.proc_gen.surface_terrain_ids[self.item_holding]
            self.proc_gen.surface_terrain_hardness_map[x, y] = SURFACE_TERRAIN[self.item_holding]['hardness']
        else:
            self.proc_gen.tile_map[x, y, z] = self.proc_gen.tile_ids[self.item_holding]
            if self.item_holding not in LIQUIDS:
                self.proc_gen.tile_hardness_map[x, y, z] = SOLID_TILES[self.item_holding]['hardness']
            
            self.proc_gen.z_map[x, y] += 1
            if z in self.proc_gen.z_dif_map:
                self.proc_gen.update_z_dif_map_tile(x, y, z, self.proc_gen.z_map[x, y])
            
            self.ui.mini_map.update_chunk_img_cache_key(x, y, z, self.proc_gen.z_map[x, y])
            self.chunk_renderer.update_chunk_img_cache_key(x, y, z, self.proc_gen.z_map[x, y])

        self.ui.mini_map.update_tile_in_chunk(x, y, z, self.item_holding)
        self.chunk_renderer.update_tile_in_chunk(x, y, self.item_holding)
        self.update_inv(self.item_holding, remove=True) # keep this last in case it changes item_holding

    def render_item_holding(self):
        if self.item_holding_img is None or self.item_holding_img.width != self.cam.screen_tile_size: 
            self.update_item_holding_img()
        
        xy = self.rect.midleft if self.facing_dir == 'left' else self.rect.midright + pg.Vector2(5,0)
        self.screen.blit(self.item_holding_bg, xy, special_flags=pg.BLEND_RGB_ADD)
        self.screen.blit(self.item_holding_img, xy)

    def update_item_holding_img(self):
        if self.item_holding is not None:
            tile_size_scaled = (TILE_SIZE * 0.75) * self.cam.zoom_scale
            self.item_holding_img = pg.transform.scale(self.assets.get_img(self.item_holding).copy(), pg.Vector2(tile_size_scaled))
            self.item_holding_img.set_colorkey((0,0,0))
            self.item_holding_img.set_alpha(200)
            self.item_holding_bg = pg.transform.scale(self.item_holding_bg, pg.Vector2(tile_size_scaled))

    def update(self):
        for alarm in self.alarms.values():
            alarm.update()

        if self.item_holding is not None:
            self.render_item_holding()
        else:
            self.item_holding_img, self.item_holding_offset = None, None