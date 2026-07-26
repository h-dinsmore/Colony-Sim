import pygame as pg
from random import randint, choice

from settings import MONTHS_DAYS, TILE_SIZE, TILE_REACH_RADIUS, TREES, FPS, SURFACE_TERRAIN

class Villager(pg.sprite.Sprite):
    def __init__(self, img_folder, xyz, spr_groups, screen, proc_gen, chunk_renderer, village):
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
        
        self.item_holding = None
        self.facing_dir = 'left'
        self.visible = True
        self.biome_in = proc_gen.id_biomes[int(proc_gen.biome_map[self.x, self.y])]
        self.alarms = {}

        self.inv = {}
        self.num_inv_slots = 64
        self.max_slot_storage = 64

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

    def check_reachable_tile(self, x, y, z):
        return (not self.proc_gen.id_tiles[self.proc_gen.tile_map[x, y, z]] == 'air') and \
            abs(self.x - x) <= TILE_REACH_RADIUS and abs(self.y - y) <= TILE_REACH_RADIUS and \
            ((abs(self.z - z) <= TILE_REACH_RADIUS) if self.chunk_renderer.view != 'z slice' else z == self.proc_gen.z_map[x, y])

    def remove_tile(self, x, y, z):
        name = self.chunk_renderer.get_tile_name(x, y)
        surface_terrain = name in SURFACE_TERRAIN
        hardness_map = self.proc_gen.surface_terrain_hardness_map if surface_terrain else self.proc_gen.tile_hardness_map
        idx = (x, y) if surface_terrain else (x, y, z)

        if hardness_map[idx] > 0:
            hardness_map[idx] -= min(hardness_map[idx], int((self.strength * self.get_tool_strength()) / FPS))
        if hardness_map[idx] == 0:
            self.add_item_to_inv(name)
            old_surface_z = int(self.proc_gen.z_map[x, y])
            self.proc_gen.update_maps_after_removed_tile(x, y, z, name) # update the tile map before the chunk renderer to show the tile below
            if (x, y) == (self.x, self.y) and (new_surface_z := int(self.proc_gen.z_map[x, y])) < old_surface_z:
                self.z = new_surface_z
                self.living = new_surface_z > -1
        
        self.chunk_renderer.update_tile_in_chunk(x, y, hardness_map[idx], name)

    def get_tool_strength(self):
        if self.item_holding is None:
            return 10
        else:
            pass

    def add_item_to_inv(self, tile_name):
        item_name = tile_name if tile_name not in TREES else 'wood'
        item_amount = 1 if item_name != 'wood' else 4
        if item_name not in self.inv and len(self.inv) < self.num_inv_slots:
            self.inv[item_name] = {'amount': item_amount, 'idx': len(self.inv)}
            if self in self.village.player_spr:
                self.village.ui.player_inv_ui.num_slots_filled += 1
                self.village.ui.player_inv_ui.item_names.append(item_name)
        else:
            if (item_amount := min(self.max_slot_storage, self.inv[item_name]['amount'] + item_amount)) <= self.max_slot_storage:
                self.inv[item_name]['amount'] = item_amount
            else: # update the dictionary to have each slot of the same item be <name> 0,1,... and check if there's any remaining wood from the slot reaching its capacity
                pass

    def update(self):
        for alarm in self.alarms.values():
            alarm.update()