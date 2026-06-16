import numpy as np
import noise
from random import randint, choice

from settings import *

class ProcGen:
    def __init__(self, keyboard, seed=randint(1000, 5000)):
        self.keyboard = keyboard
        self.seed = seed
        
        self.noise_arr_dtype = np.float32
        self.geo_maps = {}
        for k in WORLD_GEN_NOISE:
            self.geo_maps[k] = self.get_noise_arr(k)
        
        self.biome_ids, self.id_biomes = {}, {}
        for i, k in enumerate(BIOMES):
            self.biome_ids[k] = i
            self.id_biomes[i] = k
            
        self.tile_ids, self.id_tiles = {'air': 0}, {0: 'air'}
        for i, k in enumerate(SOLID_TILES.keys() | ELEVATIONS | TREES | LIQUIDS | SURFACE_TERRAIN):
            self.tile_ids[k] = i + 1
            self.id_tiles[i + 1] = k

        self.biome_map = self.get_biome_map()
        self.biome_surface_heights = {biome: None for biome in BIOMES}
        self.placed_biomes = set()
        self.tile_map = self.get_tile_map()
        self.biome_in = None
        self.x, self.y, self.z = 0, 0, MAP_TILE_SIZE[2] - 1  
    
    def get_noise_arr(self, map_name):
        arr = np.empty(MAP_TILE_SIZE[:2], dtype=self.noise_arr_dtype)
        noise_params = WORLD_GEN_NOISE[map_name]
        for x in range(MAP_TILE_SIZE[0]):
            for y in range(MAP_TILE_SIZE[1]):
                arr[x, y] = noise.pnoise2(
                    x / noise_params['scale'],
                    y / noise_params['scale'],
                    noise_params['octaves'],
                    noise_params['persistence'],
                    noise_params['lacunarity'],
                    base=self.seed
                )

        if map_name == 'surface height':
            arr += self.geo_maps['elev'] * 0.25

        return self.normalize_arr(arr)
    
    def normalize_arr(self, arr):
        arr_min = arr.min()
        arr = (arr - arr_min) / (arr.max() - arr_min)
        return arr
    
    def get_biome_map(self):
        biome_map = np.empty(MAP_TILE_SIZE[:2], dtype=np.uint8)
        biome_fitness = np.zeros((len(BIOMES), *MAP_TILE_SIZE[:2]), dtype=self.noise_arr_dtype)
        for i, biome in enumerate(BIOMES):
            for noise_k in BIOMES[biome]['geo noise']: 
                target_min, target_max = BIOMES[biome]['geo noise'][noise_k]
                dist_below_min = np.maximum(target_min - self.geo_maps[noise_k], 0)
                dist_above_max = np.maximum(self.geo_maps[noise_k] - target_max, 0)
                mean_dist = np.abs((target_min + target_max) / 2 - self.geo_maps[noise_k])
                biome_fitness[i, :, :] += dist_below_min + dist_above_max + mean_dist 
        
        biome_map = np.argmin(biome_fitness, axis=0) # choosing the biome indexes that had the least distance from its noise parameters
        return biome_map
    
    def get_tile_map(self):
        tile_map = np.zeros(MAP_TILE_SIZE, dtype=np.uint8)
        noise_map = np.zeros(MAP_TILE_SIZE, dtype=np.float32)
        for x in range(MAP_TILE_SIZE[0]):
            for y in range(MAP_TILE_SIZE[1]): 
                biome = self.id_biomes[self.biome_map[x, y]]
                noise_params = BIOMES[biome]['surface noise']
                
                if self.biome_surface_heights[biome] is None:
                    self.biome_surface_heights[biome] = self.get_biome_surface_heights(biome)

                for z in range(MAP_TILE_SIZE[2] - self.biome_surface_heights[biome].max(), MAP_TILE_SIZE[2]): 
                    noise_map[x, y, z] = noise.pnoise2(
                        x / noise_params['scale'],
                        y / noise_params['scale'],
                        noise_params['octaves'],
                        noise_params['persistence'],
                        noise_params['lacunarity'],
                        base=self.seed
                    )
        
        noise_map = self.normalize_arr(noise_map)
        self.placed_biomes = set(b for b in BIOMES if self.biome_surface_heights[b] is not None)
        self.place_solid_tiles(tile_map, noise_map)
        self.place_surface_terrain(tile_map)
        return tile_map
    
    def get_biome_surface_heights(self, biome):
        surface_height_noise = self.geo_maps['surface height'][self.biome_map == self.biome_ids[biome]]
        z_lvls = round(MAP_TILE_SIZE[2] * surface_height_noise.max())
        return (surface_height_noise * z_lvls).astype(np.uint8)
    
    def place_solid_tiles(self, tile_map, noise_map):
        for biome in self.placed_biomes:
            surface_height = min(self.biome_surface_heights[biome].max(), MAP_TILE_SIZE[2])
            min_z = MAP_TILE_SIZE[2] - surface_height # the bottom of the world is labeled z level 0 but for indexing the noise map 0 is the top
            biome_mask = self.biome_map[:, :, None] == self.biome_ids[biome] # adding an extra axis to broadcast with the noise map
            
            for z_pct, tile_data in BIOMES[biome]['z layers'].items():
                max_z = min(int(surface_height * z_pct), surface_height)
                noise_slice = noise_map[:, :, min_z:max_z] 
                
                for tile, (noise_min, noise_max) in tile_data.items():
                    tile_map[:, :, min_z:max_z][biome_mask & (noise_slice > noise_min) & (noise_slice < noise_max)] = self.tile_ids[tile]    
                
                min_z = max_z

    def place_surface_terrain(self, tile_map):
        for biome in self.placed_biomes:
            biome_mask = self.biome_map == self.biome_ids[biome]
            surface_tiles = tile_map[:, :, MAP_TILE_SIZE[2] - 1] == biome_mask
            
            for tile, (noise_min, noise_max) in BIOMES[biome]['surface terrain'].items():
                if (tile_id := self.get_biome_tile_id(biome, tile, noise_min, noise_max)):
                    tile_map[:, :, MAP_TILE_SIZE[2] - 1][
                        surface_tiles & (self.geo_maps['veg'] > noise_min) & (self.geo_maps['veg'] < noise_max)
                    ] = tile_id
                else: # keep the surface tile
                    continue

    def get_biome_tile_id(self, biome, tile, noise_min, noise_max):
        if tile in {'snow', 'small rock', 'large rock', 'small mushroom', 'large mushroom', 'cactus'}:
            return self.tile_ids[tile] # they don't change with the biomes
        
        if tile in {'plant', 'grass'}:
            return self.tile_ids[f'{biome} {tile}']
        
        for tree, noise_range in BIOMES[biome]['tree variants'].items():
            if noise_range[0] > noise_min and noise_range[1] < noise_max:
                return self.tile_ids[f'{tree} {choice((0, 1))}'] if tree in {'maple', 'fir'} else self.tile_ids[tree]

    def check_keyboard(self):
        if self.keyboard.pressed_keys[KEY_BINDINGS['+x']]:
            self.x = (self.x + 10) % MAP_TILE_SIZE[0]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-x']]:
            self.x = (self.x - 10) % MAP_TILE_SIZE[0]

        if self.keyboard.pressed_keys[KEY_BINDINGS['+y']]:
            self.y = (self.y + 10) % MAP_TILE_SIZE[1]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-y']]:
            self.y = (self.y - 10) % MAP_TILE_SIZE[1]
        
        if self.keyboard.pressed_keys[KEY_BINDINGS['+z']]:
            self.z = (self.z + 1) % MAP_TILE_SIZE[2]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-z']]:
            self.z = (self.z - 1) % MAP_TILE_SIZE[2]     

    def update(self):
        self.check_keyboard()