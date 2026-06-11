import numpy as np
import noise
from random import randint

from settings import *

class ProcGen:
    def __init__(self, keyboard, seed=randint(1000, 5000)):
        self.keyboard = keyboard
        self.seed = seed
        
        self.tile_ids, self.id_tiles = {'air': 0}, {0: 'air'}
        for i, k in enumerate(SURFACES.keys() | ELEVATIONS | TREES | LIQUIDS):
            self.tile_ids[k] = i + 1
            self.id_tiles[i + 1] = k

        self.biome_ids, self.id_biomes = {}, {}
        for i, k in enumerate(BIOMES):
            self.biome_ids[k] = i
            self.id_biomes[i] = k
        self.biome_in = None
        self.x, self.y, self.z = 0, 0, 0

        self.noise_arr_dtype = np.float32
        self.geo_maps = {}
        for k in WORLD_GEN_NOISE:
            self.geo_maps[k] = self.get_noise_arr(k)

        self.biome_map = self.get_biome_map()
        self.tile_map = self.get_tile_map()
    
    def get_noise_arr(self, map_name):
        arr = np.empty((MAP_SIZE), dtype=self.noise_arr_dtype)
        noise_params = WORLD_GEN_NOISE[map_name]
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                arr[x, y, :] = noise.pnoise2(
                    x / noise_params['scale'],
                    y / noise_params['scale'],
                    noise_params['octaves'],
                    noise_params['persistence'],
                    noise_params['lacunarity'],
                    base=self.seed
                )
        return self.normalize_arr(arr)
    
    def normalize_arr(self, arr):
        arr_min = arr.min()
        arr = (arr - arr_min) / (arr.max() - arr_min)
        return arr
    
    def get_map_val_pct_max(self, map_name, x, y):
        geo_map = self.geo_maps[map_name]
        max_val = geo_map.max()
        return (max_val - map[x, y, :]) / max_val
    
    def get_biome_map(self):
        biome_map = np.empty(MAP_SIZE, dtype=np.int8)
        biome_fitness = np.zeros((len(BIOMES), *MAP_SIZE), dtype=self.noise_arr_dtype)
        for i, biome in enumerate(BIOMES):
            for noise_k in BIOMES[biome]['geo noise']: 
                noise_map = self.geo_maps[noise_k]
                target_min, target_max = BIOMES[biome]['geo noise'][noise_k]
                dist_below_min, dist_above_max = np.maximum(target_min - noise_map, 0), np.maximum(noise_map - target_max, 0)
                mean_dist = np.abs((target_min + target_max) / 2 - noise_map) 
                biome_fitness[i, :, :, :] += dist_below_min + dist_above_max + mean_dist 
        biome_map = np.argmin(biome_fitness, axis=0) # choosing the biome indexes that had the least distance from its noise parameters
        return biome_map
    
    def get_tile_map(self):
        tile_map = np.zeros(MAP_SIZE, dtype=np.int16)
        noise_map = np.empty(MAP_SIZE, dtype=np.float32)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                for z in range(MAP_SIZE[2]):
                    noise_params = BIOMES[self.id_biomes[self.biome_map[x, y, z]]]['surface noise']
                    noise_map[x, y, z] = noise.pnoise2(
                        x / noise_params['scale'],
                        y / noise_params['scale'],
                        noise_params['octaves'],
                        noise_params['persistence'],
                        noise_params['lacunarity'],
                        base=self.seed
                    )
        self.place_tiles(tile_map, self.normalize_arr(noise_map))
        return tile_map
    
    def place_tiles(self, tile_map, noise_map):
        z_lvls = MAP_SIZE[2]
        for biome in BIOMES:
            min_z = 0
            biome_noise = np.where(self.biome_map == self.biome_ids[biome], noise_map, np.nan)
            for z_pct, tiles in BIOMES[biome]['z layers'].items():
                max_z = min(int(z_lvls * z_pct), z_lvls - 1)
                z_slice = biome_noise[:, :, min_z:max_z] 
                for tile, (tmin, tmax) in tiles.items():
                    tile_map[:, :, min_z:max_z][(z_slice > tmin) & (z_slice < tmax)] = self.tile_ids[tile]
                min_z = max_z

    def update(self):
        if self.keyboard.pressed_keys[KEY_BINDINGS['+x']]:
            self.x = (self.x + 1) % MAP_SIZE[0]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-x']]:
            self.x = (self.x - 1) % MAP_SIZE[0]

        if self.keyboard.pressed_keys[KEY_BINDINGS['+y']]:
            self.y = (self.y + 1) % MAP_SIZE[1]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-y']]:
            self.y = (self.y - 1) % MAP_SIZE[1]
        
        if self.keyboard.pressed_keys[KEY_BINDINGS['+z']]:
            self.z = (self.z + 1) % MAP_SIZE[2]
        if self.keyboard.pressed_keys[KEY_BINDINGS['-z']]:
            self.z = (self.z - 1) % MAP_SIZE[2]     