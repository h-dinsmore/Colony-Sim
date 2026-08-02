import pygame as pg
from math import ceil

from settings import *

class ChunkRenderer:
    def __init__(self, world_surf, proc_gen, assets, cam, keyboard):
        self.world_surf = world_surf
        self.proc_gen = proc_gen
        self.assets = assets
        self.cam, self.prev_cam_offset = cam, pg.Vector2()
        self.keyboard = keyboard
        self.player = None # not initialized yet
        
        self.view, self.view_types = 'surface', ('elevation', 'surface', 'z slice')
        self.prev_z, self.prev_view = None, None

        self.num_chunk_tiles = 32
        self.chunk_px_size = self.num_chunk_tiles * TILE_SIZE
        self.visible_chunks = []
        max_chunk_idx = (pg.Vector2(MAP_TILE_SIZE[:2]) - pg.Vector2(self.num_chunk_tiles)) // self.num_chunk_tiles
        self.max_chunk_idx = (int(max_chunk_idx.x), int(max_chunk_idx.y))
        self.chunk_img_cache = {k: {} for k in self.view_types}
        
    def render(self):
        if new_cam_offset := self.cam.offset != self.prev_cam_offset:
            self.prev_cam_offset = self.cam.offset.copy()

        if new_view := self.prev_view != self.view:
            self.prev_view = self.view
        
        if new_z_lvl := self.player.z != self.prev_z:
            self.prev_z = self.player.z
            if self.player.z not in self.proc_gen.z_dif_map:
                self.proc_gen.update_z_dif_map(self.player.z)
        
        if new_cam_offset or new_view or (new_z_lvl and self.view != 'surface'): # the same tiles are shown for the surface view if the z level changes
            self.visible_chunks = self.get_visible_chunks()
                
        cache = self.chunk_img_cache[self.view]
        for chunk_xyz in self.visible_chunks:
            self.world_surf.blit(
                cache[chunk_xyz] if chunk_xyz in cache else self.get_chunk_img(*chunk_xyz), 
                pg.Vector2(chunk_xyz[:2]) * self.chunk_px_size
            )
        
    def get_visible_chunks(self):
        chunks = []
        start_chunk_idx = (self.cam.offset // TILE_SIZE) // self.num_chunk_tiles
        start_chunk_idx = int(start_chunk_idx.x), int(start_chunk_idx.y)
        start_chunk_tile = start_chunk_idx[0] * self.num_chunk_tiles, start_chunk_idx[1] * self.num_chunk_tiles
     
        num_chunks_x = ceil(ceil(SCREEN_TILES[0] / self.cam.zoom_scale) / self.num_chunk_tiles)
        num_chunks_y = ceil(ceil(SCREEN_TILES[1] / self.cam.zoom_scale) / self.num_chunk_tiles)
        end_chunk_idx = (
            min(start_chunk_idx[0] + num_chunks_x, self.max_chunk_idx[0]),
            min(start_chunk_idx[1] + num_chunks_y, self.max_chunk_idx[1])
        )
      
        z_slice_view = self.view == 'z slice'
        for x in range((end_chunk_idx[0] - start_chunk_idx[0]) + 1):
            for y in range((end_chunk_idx[1] - start_chunk_idx[1]) + 1):
                chunk_tile_x = start_chunk_tile[0] + (x * self.num_chunk_tiles)
                chunk_tile_y = start_chunk_tile[1] + (y * self.num_chunk_tiles)
                chunk_tile_z = self.player.z if z_slice_view else int(self.proc_gen.z_map[chunk_tile_x, chunk_tile_y])
                chunk_idx = start_chunk_idx[0] + x, start_chunk_idx[1] + y, chunk_tile_z
                chunks.append(chunk_idx)
        return chunks
      
    def get_chunk_img(self, chunk_x, chunk_y, chunk_z):
        img = pg.Surface((self.chunk_px_size, self.chunk_px_size), pg.SRCALPHA)

        if self.view == 'elevation' and self.player.z not in self.proc_gen.z_dif_map:
            self.proc_gen.update_z_dif_map(self.player.z)

        tile_x = min(chunk_x * self.num_chunk_tiles, self.max_chunk_idx[0] * self.num_chunk_tiles)
        tile_y = min(chunk_y * self.num_chunk_tiles, self.max_chunk_idx[1] * self.num_chunk_tiles)
        for x in range(img.width // TILE_SIZE):
            for y in range(img.height // TILE_SIZE):
                if (tile_name := self.get_tile_name(tile_x + x, tile_y + y)) != 'air':
                    img.blit(self.assets.get_img(tile_name), (x * TILE_SIZE, y * TILE_SIZE))
        
        self.chunk_img_cache[self.view][(chunk_x, chunk_y, chunk_z)] = img
        return img

    def update_tile_in_chunk(self, tile_x, tile_y, name, hardness=None):
        chunk_x, chunk_y = tile_x // self.num_chunk_tiles, tile_y // self.num_chunk_tiles
        chunk_key = (chunk_x, chunk_y, int(self.proc_gen.z_map[chunk_x * self.num_chunk_tiles, chunk_y * self.num_chunk_tiles]))
        px_xy_in_chunk = (pg.Vector2(tile_x, tile_y) * TILE_SIZE) - (pg.Vector2(chunk_x, chunk_y) * self.chunk_px_size)
        for view in (v for v in self.view_types if chunk_key in self.chunk_img_cache[v]):
            self.chunk_img_cache[view][chunk_key].blit(self.get_tile_below_img(view, tile_x, tile_y, name, hardness), px_xy_in_chunk)

    def get_tile_z_idx(self, tile_x, tile_y):
        match self.view:
            case 'surface': 
                return self.proc_gen.z_map[tile_x, tile_y]

            case 'z slice': 
                return self.player.z

            case 'elevation': 
                return self.proc_gen.z_dif_map[self.player.z][tile_x, tile_y]

    def get_tile_below_img(self, view, x, y, name, hardness=None):
        if name == 'air' or view == 'z slice':
            img = self.get_air_tile_img()
        else: 
            if view == 'surface':
                if self.proc_gen.z_map[x, y] == 0:
                    img = self.get_air_tile_img()
                else:
                    img = self.assets.get_img(name).copy()
                    if hardness is not None and hardness > 0: # else the tile below will be shown at full alpha
                        img.set_alpha(int(255 * (hardness / (SOLID_TILES if name in SOLID_TILES else SURFACE_TERRAIN)[name]['hardness'])))
            else: 
                if hardness != 0 or self.proc_gen.z_map[x, y] == self.player.z: 
                    img = self.assets.graphics['terrain'].files[name].copy()
                    if hardness is not None:
                        img.set_alpha(int(255 * (hardness / (SOLID_TILES if name in SOLID_TILES else SURFACE_TERRAIN)[name]['hardness'])))
                else: 
                    img = self.assets.graphics['terrain'].files[self.proc_gen.id_tiles[self.proc_gen.z_dif_map[self.player.z][x, y]]]
        return img
    
    def get_air_tile_img(self):
        img = pg.Surface((self.cam.screen_tile_size, self.cam.screen_tile_size), pg.SRCALPHA)
        img.fill(self.assets.colors['transparent'])
        return img

    def get_tile_name(self, x, y):
        name = 'air'
        tile_z = int(self.proc_gen.z_map[x, y])
        if self.view == 'z slice':
            if self.player.z == tile_z and (surface_terrain_id := self.proc_gen.surface_terrain_map[x, y]) > 0:
                name = self.proc_gen.id_surface_terrain[surface_terrain_id]
            else:
                name = self.proc_gen.id_tiles[self.proc_gen.tile_map[x, y, self.player.z]]
        else:
            surface_terrain_id = self.proc_gen.surface_terrain_map[x, y]
            if self.view == 'surface':
                if surface_terrain_id > 0:
                    name = self.proc_gen.id_surface_terrain[surface_terrain_id]
                else:
                    name = self.proc_gen.id_tiles[self.proc_gen.tile_map[x, y, tile_z]]
            else:
                if self.player.z == tile_z and surface_terrain_id > 0:
                    name = self.proc_gen.id_surface_terrain[surface_terrain_id]
                else:
                    name = self.proc_gen.id_tiles[self.proc_gen.z_dif_map[self.player.z][x, y]]
        return name

    def get_cache(self):
        match self.view:
            case 'z slice': 
                return self.z_slice_cache

            case 'elevation': 
                return self.elev_view_cache

            case 'surface': 
                return self.surface_view_cache

    def update_chunk_img_cache_key(self, x, y, old_z, new_z):
        chunk_x, chunk_y = x // self.num_chunk_tiles, y // self.num_chunk_tiles
        for view in (v for v in self.view_types if (chunk_x, chunk_y, old_z) in self.chunk_img_cache[v]):
            img = self.chunk_img_cache[view][(chunk_x, chunk_y, old_z)]
            del self.chunk_img_cache[view][(chunk_x, chunk_y, old_z)]
            self.chunk_img_cache[view][(chunk_x, chunk_y, new_z)] = img

    def update(self):
        for view_type in self.view_types:
            if self.keyboard.pressed_keys[KEY_BINDINGS[f'{view_type} view']]:
                self.view = view_type

        self.render()