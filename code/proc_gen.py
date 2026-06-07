import numpy as np
import noise
from random import randint

from settings import *

class ProcGen:
    def __init__(self, keyboard, seed=randint(1000, 5000)):
        self.keyboard = keyboard
        self.seed = seed
        
        self.tile_ids = {'air': 0}
        self.id_names = {0: 'air'}
        for i, k in enumerate(SURFACES.keys() | ELEVATIONS | TREES | LIQUIDS):
            self.tile_ids[k] = i + 1
            self.id_names[i + 1] = k

        self.biome_ids = {k: i + 1 for i, k in enumerate(BIOMES)}
        self.biome_in = None
        self.x, self.y, self.z = 0, 0, 0

        self.noise_scale_x, self.noise_scale_y = (MAP_SIZE[0] // 10, MAP_SIZE[1] // 10)
        self.weather_data = {}
        self.elev_map = self.get_elev_map()
        self.temp_map = self.get_temp_map()
        self.precip_map = self.get_precip_map()
        self.plants_map = self.get_plants_map()
        self.biome_map = self.get_biome_map()
        self.tile_map = self.get_tile_map()
        
    def get_dist_equator(self, y):
        equator = MAP_SIZE[1] / 2
        return abs(equator - y) / equator 
    
    def get_rel_max(self, name, x, y):
        max_num = self.weather_data[name]['max num']
        return (max_num - self.weather_data[name]['map'][x, y]) / max_num
    
    def get_elev_map(self):
        elev_map = np.empty((MAP_SIZE[0], MAP_SIZE[1]), dtype=np.float32)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                elev_map[x, y] = noise.pnoise2(
                    x / self.noise_scale_x,
                    y / self.noise_scale_y,
                    base=self.seed
                )

        self.weather_data['elev'] = {'map': elev_map, 'max num': elev_map.max()}
        return elev_map
    
    def get_temp_map(self):
        temp_map = np.empty((MAP_SIZE[0], MAP_SIZE[1]), dtype=np.float32)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                temp_map[x, y] = self.get_dist_equator(y) * self.get_rel_max('elev', x, y)

        self.weather_data['temp'] = {'map': temp_map, 'max num': temp_map.max()}
        return temp_map

    def get_precip_map(self):
        precip_map = np.empty((MAP_SIZE[0], MAP_SIZE[1]), dtype=np.float32)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                precip_map[x, y] = self.get_dist_equator(y) * self.get_rel_max('temp', x, y) * self.get_rel_max('elev', x, y)

        self.weather_data['precip'] = {'map': precip_map, 'max num': precip_map.max()}
        return precip_map

    def get_plants_map(self):
        plants_map = np.empty((MAP_SIZE[0], MAP_SIZE[1]), dtype=np.float32)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                plants_map[x, y] = self.get_dist_equator(y) * self.get_rel_max('precip', x, y) * self.get_rel_max('elev', x, y) 

        self.weather_data['plants'] = {'map': plants_map, 'max num': plants_map.max()}
        return plants_map
    
    def get_biome_map(self):
        biome_map = np.empty((MAP_SIZE[0], MAP_SIZE[1]), dtype=np.int8)
        for k, i in self.biome_ids.items():
            nmax = BIOMES[k]['noise max']
            biome_map[
                (self.elev_map < nmax['elev']) & (self.temp_map < nmax['temp']) & (self.precip_map < nmax['precip']) &
                (self.plants_map < nmax['plants'])
            ] = i
        return biome_map
    
    def get_tile_map(self):
        tile_map = np.zeros(MAP_SIZE, dtype=np.int16)
        noise_map = np.empty(MAP_SIZE, dtype=np.float16)
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                for z in range(MAP_SIZE[2]):
                    noise_map[x, y, z] = noise.pnoise2(
                        x / self.noise_scale_x,
                        y / self.noise_scale_y,
                        base=self.seed
                    )
        
        self.place_tiles(tile_map, noise_map)
        return tile_map
    
    def place_tiles(self, tile_map, noise_map):
        z_lvls = MAP_SIZE[2]
        for k in self.biome_ids:
            min_z = 0
            for z_pct, tile_pcts in BIOMES[k]['z lvl slices'].items():
                max_z = int(z_lvls * z_pct)
                z_slice = noise_map[:, :, min_z:min(max_z, z_lvls - 1)] 
                for tile in tile_pcts:
                    tile_map[:, :, min_z:min(max_z, z_lvls - 1)][z_slice < tile_pcts[tile]] = self.tile_ids[tile]
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