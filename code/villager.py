import pygame as pg
from random import randint, choice

from settings import MONTHS_DAYS, TILE_SIZE, TILE_REACH_RADIUS, TREES, FPS, SURFACE_TERRAIN

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
        self.item_holding, self.item_holding_img, self.item_holding_offset = None, None, None
        self.item_holding_outline_w = 1
        
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
            self.add_item_to_inv(name)
            old_surface_z = int(self.proc_gen.z_map[x, y])
            self.proc_gen.update_maps_after_removed_tile(x, y, z, name) # update the tile map before the chunk renderer to show the tile below
            name = self.chunk_renderer.get_tile_name(x, y)
            self.ui.mini_map.update_tile_in_chunk(x, y, name) # only updating after a removed tile bc it doesn't render alphas like the chunk renderer
            
            if (new_surface_z := int(self.proc_gen.z_map[x, y])) < old_surface_z:
                if (x, y) == (self.x, self.y):
                    self.z = new_surface_z
                    self.living = new_surface_z > -1

                if old_surface_z in self.proc_gen.z_dif_map:
                    self.proc_gen.update_z_dif_map_tile(x, y, old_surface_z, new_surface_z)

            if self.is_player:
                self.tile_remove_check = False
                self.alarms['update tile remove check'].start()
        
        self.chunk_renderer.update_tile_in_chunk(x, y, hardness_map[idx], name)

    def get_tool_strength(self):
        if self.item_holding is None:
            return 1
        else:
            pass

    def add_item_to_inv(self, tile_name):
        item_name = tile_name if tile_name not in TREES else 'wood'
        item_amount = 1 if item_name != 'wood' else 4
        if item_name not in self.inv and len(self.inv) < self.num_inv_slots:
            self.inv[item_name] = {'amount': item_amount, 'idx': len(self.inv)}
            if self.is_player:
                self.ui.player_inv_ui.num_slots_filled += 1
                self.ui.player_inv_ui.item_names.append(item_name)
        else:
            if (item_amount := min(self.max_slot_storage, self.inv[item_name]['amount'] + item_amount)) <= self.max_slot_storage:
                self.inv[item_name]['amount'] = item_amount
            else: # update the dictionary to have each slot of the same item be <name> 0,1,... and check if there's any remaining wood from the slot reaching its capacity
                pass

    def place_tile(self, x, y, z):
        pass

    def render_item_holding(self):
        if self.item_holding_img is None or self.item_holding_img.width != self.cam.screen_tile_size: 
            self.update_item_holding_img()

        self.screen.blit(
            self.item_holding_img, 
            self.rect.center + (self.item_holding_offset if self.facing_dir == 'right' else -self.item_holding_offset)
        )

    def update_item_holding_img(self):
        if self.item_holding is not None:
            tile_size_scaled = TILE_SIZE * self.cam.zoom_scale
            self.item_holding_img = pg.transform.scale(self.assets.get_img(self.item_holding), pg.Vector2(tile_size_scaled))
            self.item_holding_img.set_alpha(128)
            self.item_holding_offset = pg.Vector2(tile_size_scaled / 2, 0)

    def update(self):
        for alarm in self.alarms.values():
            alarm.update()

        if self.item_holding is not None:
            self.render_item_holding()
        else:
            self.item_holding_img, self.item_holding_outline = None, None