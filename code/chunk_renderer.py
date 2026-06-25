import pygame as pg
from math import ceil

from settings import *

class ChunkRenderer:
    def __init__(self, world_surf, proc_gen, assets, cam, player):
        self.world_surf = world_surf
        self.proc_gen = proc_gen
        self.assets = assets
        self.cam = cam 
        self.prev_cam_offset = pg.Vector2()
        self.player = player
        
        self.chunk_tile_size = 32
        self.chunk_px_size = self.chunk_tile_size * TILE_SIZE
        self.visible_chunks = []
        self.cache, self.z_dif_cache = {}, {}
        self.max_chunk_px_x, self.max_chunk_px_y = MAP_PX_SIZE[0] // self.chunk_px_size, MAP_PX_SIZE[1] // self.chunk_px_size
        self.prev_z_lvl = None
        self.z_dif_view = False
        
        self.terrain_types = {
            'solid tiles': SOLID_TILES.keys(), 
            'surface terrain': SURFACE_TERRAIN,
            'elevations': ELEVATIONS, 
            'trees': TREES, 
            'liquids': LIQUIDS
        }

    def render(self):
        new_cam_offset = self.cam.offset != self.prev_cam_offset
        new_z_lvl = self.player.z != self.prev_z_lvl
        z_dif_view_change = self.proc_gen.z_dif_view != self.z_dif_view
        if new_cam_offset or new_z_lvl or z_dif_view_change:
            self.visible_chunks = self.get_visible_chunks()

            if new_cam_offset:
                self.prev_cam_offset = self.cam.offset.copy()

            if new_z_lvl:
                self.prev_z_lvl = self.player.z

            if z_dif_view_change:
                self.z_dif_view = self.proc_gen.z_dif_view

        cache = self.cache if not self.proc_gen.z_dif_view else self.z_dif_cache
        for xyz in self.visible_chunks:
            self.world_surf.blit(cache[xyz] if xyz in cache else self.get_chunk_img(*xyz), xyz[:2])
        
    def get_visible_chunks(self):
        screen_chunks_x = (ceil(RES[0] / self.cam.zoom_scale) // self.chunk_px_size) + 2
        screen_chunks_y = (ceil(RES[1] / self.cam.zoom_scale) // self.chunk_px_size) + 2
        
        offset_x, offset_y = self.cam.offset
        start_x = max(0, min(int(offset_x) // self.chunk_px_size, self.max_chunk_px_x))
        start_y = max(0, min(int(offset_y) // self.chunk_px_size, self.max_chunk_px_y))
        
        return [
            ((start_x + x) * self.chunk_px_size, (start_y + y) * self.chunk_px_size, self.player.z)
            for x in range(screen_chunks_x) for y in range(screen_chunks_y) 
        ]
      
    def get_chunk_img(self, chunk_x, chunk_y, chunk_z):
        img = pg.Surface((
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[0] - chunk_x)), 
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[1] - chunk_y))
        ), pg.SRCALPHA)

        tile_x, tile_y = chunk_x // TILE_SIZE, chunk_y // TILE_SIZE
        for x in range(img.width // TILE_SIZE):
            for y in range(img.height // TILE_SIZE):
                tile_coords = (tile_x + x, tile_y + y, chunk_z)
                if (terrain_id := self.proc_gen.tile_map[tile_coords]) == self.proc_gen.tile_ids['air']:
                    if self.proc_gen.z_dif_view and (elev_id := self.proc_gen.z_dif_map[tile_coords[:2]]) != 0:
                        img.blit(self.assets.get_img(self.get_img_path(elev_id)), (x * TILE_SIZE, y * TILE_SIZE))
                else:
                    img.blit(self.assets.get_img(self.get_img_path(terrain_id)), (x * TILE_SIZE, y * TILE_SIZE))

        if self.proc_gen.z_dif_view:
            self.z_dif_cache[(chunk_x, chunk_y, chunk_z)] = img
        else:
            self.cache[(chunk_x, chunk_y, chunk_z)] = img
        
        return img
    
    def get_img_path(self, tile_id):
        img_name = self.proc_gen.id_tiles[tile_id]
        path = '../graphics/terrain/'
        for k in self.terrain_types:
            if img_name in self.terrain_types[k]:
                return path + k + f'/{img_name}.png'