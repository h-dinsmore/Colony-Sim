import numpy as np
import noise
from random import choice

from settings import *

class ProcGen:
    def __init__(self):
        self.noise_arr_dtype = np.float32
        self.geo_maps = {}
        for k in WORLD_GEN_NOISE:
            self.geo_maps[k] = self.get_noise_arr(k) 
        
        self.biome_ids, self.id_biomes = {}, {}
        for i, k in enumerate(BIOMES):
            self.biome_ids[k] = i
            self.id_biomes[i] = k
        
        self.tile_ids, self.id_tiles = {}, {}
        # storing these first to use the ids to look up tile hardness values using the tile_hardness_map indices
        for i, k in enumerate(('air', *REMOVABLE_TILES)):
            self.tile_ids[k], self.id_tiles[i] = i, k 
        
        for i, k in enumerate(ALL_TILES - REMOVABLE_TILES, start=len(self.tile_ids) + 1):
            self.tile_ids[k] = i + 1
            self.id_tiles[i + 1] = k

        self.biome_map = self.get_biome_map()
        max_z_map = np.round(self.geo_maps['max z'] * (MAP_TILE_SIZE[2] - 1)).astype(np.uint8)
        self.biome_max_z = {b: np.where(self.biome_map == self.biome_ids[b], max_z_map, 0) for b in BIOMES}
        self.placed_biomes = set(b for b in BIOMES if self.biome_max_z[b] is not None)
        
        self.tile_map = self.get_tile_map()
        self.surface_terrain_map = self.get_surface_terrain_map()
        self.tile_hardness_map = self.get_tile_hardness_map()

        self.z_map = np.max(np.where(self.tile_map != self.tile_ids['air'], np.arange(MAP_TILE_SIZE[2]), -1), axis=2).astype(np.int8)
        self.z_dif_map = {}
       
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
                    repeatx=MAP_TILE_SIZE[0],
                    repeaty=MAP_TILE_SIZE[1],
                )

        if map_name == 'max z':
            arr = np.minimum(arr + (self.geo_maps['elev'] * 0.25), 1.0)

        return self.normalize_arr(arr)
    
    def normalize_arr(self, arr):
        arr_min = arr.min()
        return (arr - arr_min) / (arr.max() - arr_min)
    
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
        noise_map = np.zeros(MAP_TILE_SIZE, dtype=self.noise_arr_dtype)
        for x in range(MAP_TILE_SIZE[0]):
            for y in range(MAP_TILE_SIZE[1]): 
                biome = self.id_biomes[self.biome_map[x, y]] 
                noise_params = BIOMES[biome]['surface noise']
                for z in range(self.biome_max_z[biome][x, y]):
                    noise_map[x, y, z] = noise.pnoise2(
                        x / noise_params['scale'],
                        y / noise_params['scale'],
                        noise_params['octaves'],
                        noise_params['persistence'],
                        noise_params['lacunarity'],
                        repeatx=MAP_TILE_SIZE[0],
                        repeaty=MAP_TILE_SIZE[1],
                    )
        self.place_solid_tiles(tile_map, self.normalize_arr(noise_map)) 
        return tile_map
    
    def place_solid_tiles(self, tile_map, noise_map):
        min_z_arr = np.zeros(MAP_TILE_SIZE, dtype=np.uint8)
        full_z_map = np.arange(MAP_TILE_SIZE[2]).reshape(1, 1, -1)
        for biome in self.placed_biomes:
            biome_mask = self.biome_map[:, :, np.newaxis] == self.biome_ids[biome]
            max_z = self.biome_max_z[biome]

            for z_pct, tile_data in BIOMES[biome]['z layers'].items():
                max_z_arr = np.round(max_z * z_pct).astype(np.uint8)[:, :, np.newaxis]
                z_mask = (full_z_map >= min_z_arr) & ((full_z_map < max_z_arr) if z_pct < 1.0 else (full_z_map <= max_z_arr))
                
                for tile, (noise_min, noise_max) in tile_data.items():
                    tile_map[biome_mask & z_mask & (noise_map > noise_min) & (noise_map < noise_max)] = self.tile_ids[tile] 
                
                min_z_arr = max_z_arr

    def get_surface_terrain_map(self):
        surface_terrain_map = np.zeros(MAP_TILE_SIZE[:2], dtype=np.uint8)
        for biome in self.placed_biomes:
            biome_mask = self.biome_map == self.biome_ids[biome]
            for tile, (noise_min, noise_max) in BIOMES[biome]['surface terrain'].items():
                if (tile_id := self.get_biome_tile_id(biome, tile, noise_min, noise_max)):
                    x, y = np.where(biome_mask & (self.geo_maps['veg'] > noise_min) & (self.geo_maps['veg'] < noise_max))
                    surface_terrain_map[x, y] = tile_id
        return surface_terrain_map
    
    def get_biome_tile_id(self, biome, tile, noise_min, noise_max):
        if tile in {'snow', 'small rock', 'large rock', 'small mushroom', 'large mushroom', 'cactus'}:
            return self.tile_ids[tile] # they don't change with the biomes
        
        if tile in {'plant', 'grass'}:
            return self.tile_ids[f'{biome} {tile}']
        
        for tree, noise_range in BIOMES[biome]['tree variants'].items():
            if noise_range[0] > noise_min and noise_range[1] < noise_max:
                return self.tile_ids[f'{tree} {choice((0, 1))}'] if tree in {'maple', 'fir'} else self.tile_ids[tree]

    def get_tile_hardness_map(self):
        tile_hardness_by_id = np.array([self.tile_ids['air']] + [TILE_HARDNESS_VALUES[tile] for tile in REMOVABLE_TILES], dtype=np.uint16) # the index of each element matches the id of the tile it represents
        return tile_hardness_by_id[self.tile_map] # TODO: add a mask for liquids when they get added

    def update_z_dif_map(self, z): # TODO: add a condition checking if any tiles were changed from the cached map when mining and tree cutting is added 
        z_map = np.where(self.z_map != -1, self.z_map, z)
        z_difs = (z_map - z).astype(np.int8)
        x, y = np.indices(z_map.shape)
        surface_tiles = self.tile_map[x, y, z_map].copy()
        for (min_dif, max_dif), tile in Z_DIF_ICONS.items():
            mask = ((z_difs >= min_dif) & (z_difs < max_dif)) if min_dif > 0 else ((z_difs <= min_dif) & (z_difs > max_dif))
            mask &= (z_difs != 0) & (z_map != 0) # ignore tiles on the same z level or air 
            surface_tiles[mask] = self.tile_ids[tile]

        self.z_dif_map[z] = surface_tiles

    def update_maps_after_removed_tile(self, x, y, old_z):
        tile_name = self.id_tiles[self.tile_map[x, y, old_z]] 
        solid_tile = tile_name in SOLID_TILES
        surface_terrain_tile = tile_name in SURFACE_TERRAIN.keys() | TREES # TODO: maybe merge the trees into surface terrain?
        self.tile_map[x, y, old_z] = self.tile_ids['air']
        new_surface_z = self.get_new_surface_z(x, y, old_z, solid_tile, surface_terrain_tile)
        self.z_map[x, y] = new_surface_z
      
        if old_z in self.z_dif_map:
            if new_surface_z == -1: # all tiles below old_z are air
                self.z_dif_map[old_z][x, y] = self.tile_ids['air']
            else:
                if (z_dif := abs(old_z - new_surface_z)) != 0:
                    for (min_dif, max_dif) in Z_DIF_ICONS:
                        if ((z_dif >= min_dif) and (z_dif < max_dif)) if min_dif > 0 else ((z_dif <= min_dif) and (z_dif > max_dif)):
                            self.z_dif_map[old_z][x, y] = self.tile_ids[Z_DIF_ICONS[(min_dif, max_dif)]]
                            break
                else:
                    self.z_dif_map[old_z][x, y] = self.tile_ids[self.tile_map[x, y, new_surface_z]]
    
    def get_new_surface_z(self, x, y, old_z, solid_tile, surface_terrain_tile):
        if solid_tile:
            new_surface_z = -1
            for z in range(old_z - 1, -1, -1):
                if self.tile_map[x, y, z] != self.tile_ids['air']:
                    new_surface_z = z
                    break
        else:
            new_surface_z = old_z - 1
            if surface_terrain_tile:
                self.surface_terrain_map[x, y] = 0

        return new_surface_z