from player import Player
from villager import Villager
from settings import MAP_TILE_SIZE, RES

import pygame as pg
import numpy as np
from random import randint

class Village:
    def __init__(self, proc_gen, assets, keyboard, screen):
        self.proc_gen = proc_gen
        self.assets = assets
        self.keyboard = keyboard
        self.screen = screen
        
        self.num_pop, self.num_max_pop = 3, 128
        self.spawn_z = None
        self.spawn_map = self.get_spawn_map()
    
        self.village_sprs = pg.sprite.Group()
        self.player_spr = pg.sprite.GroupSingle()

        player_y, player_x = np.where(self.spawn_map == 1)
        self.player = Player(
            self.assets.get_img('../graphics/entities/villagers/player/idle.png'),
            (int(player_y[0]), int(player_x[0]), self.spawn_z), 
            [self.village_sprs, self.player_spr],
            self.screen,
            self.keyboard,
            self.proc_gen
        )

        for i in range(2, self.num_pop + 1): 
            y, x = np.where(self.spawn_map == i)
            Villager(
                self.assets.get_img('../graphics/entities/villagers/idle.png'),
                (int(y[0]), int(x[0]), self.spawn_z),
                [self.village_sprs],
                self.screen,
                self.proc_gen
            )

    def get_spawn_map(self):
        spawn_map = np.zeros(MAP_TILE_SIZE[:2], dtype=np.uint8) # values > 0 will be the spawn tile for the nth villager added
        
        biome_map, biome_ids = self.proc_gen.biome_map, self.proc_gen.biome_ids
        biome_mask = (biome_map != self.proc_gen.biome_ids['desert']) & (biome_map != biome_ids['tundra'])
        valid_biome_tiles = np.argwhere(biome_mask) 
        
        z_map = self.proc_gen.z_map
        start_y, start_x = valid_biome_tiles[randint(0, valid_biome_tiles.shape[0] - 1)]
        self.spawn_z = int(z_map[start_y, start_x]) # storing as a class attribute to keep the spawn map 2d
        
        z_slice = np.argwhere(biome_mask & (z_map == self.spawn_z))
        start_idx = np.where((z_slice[:, 0] == start_y) & (z_slice[:, 1] == start_x))[0][0]
      
        for i in range(self.num_pop):
            y, x = z_slice[start_idx + i]
            spawn_map[int(y), int(x)] = i + 1

        return spawn_map
    
    def update(self):
        for spr in self.village_sprs:
            if spr.visible and spr not in self.player_spr:
                self.screen.blit(spr.image, spr.rect.center)
                
            spr.update()
        
        self.screen.blit(self.player.image, self.player.rect.center)