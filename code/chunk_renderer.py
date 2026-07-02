import pygame as pg
from math import ceil

from settings import *

class ChunkRenderer:
    def __init__(self, world_surf, proc_gen, assets, cam, player):
        self.world_surf = world_surf
        self.proc_gen = proc_gen
        self.assets = assets
        self.cam, self.prev_cam_offset = cam, pg.Vector2()
        self.player = player
        
        self.chunk_tile_size = 32
        self.chunk_px_size = self.chunk_tile_size * TILE_SIZE
        self.visible_chunks = []
        self.surface_view_cache, self.elev_view_cache, self.z_slice_cache = {}, {}, {}
        self.max_chunk_px_x, self.max_chunk_px_y = MAP_PX_SIZE[0] // self.chunk_px_size, MAP_PX_SIZE[1] // self.chunk_px_size
        self.prev_z_lvl = None
        self.view = None
        
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
        view_change = self.proc_gen.view != self.view
        if new_cam_offset or new_z_lvl or view_change:
            self.visible_chunks = self.get_visible_chunks()

            if new_cam_offset:
                self.prev_cam_offset = self.cam.offset.copy()

            if new_z_lvl:
                self.prev_z_lvl = self.player.z

            if view_change:
                self.view = self.proc_gen.view

        cache = self.get_cache()
        for xyz in self.visible_chunks:
            self.world_surf.blit(cache[xyz] if xyz in cache else self.get_chunk_img(*xyz), xyz[:2])
        
    def get_visible_chunks(self):
        start_x = max(0, min(int(self.cam.offset.x) // self.chunk_px_size, self.max_chunk_px_x))
        start_y = max(0, min(int(self.cam.offset.y) // self.chunk_px_size, self.max_chunk_px_y))
        return [
            ((start_x + x) * self.chunk_px_size, (start_y + y) * self.chunk_px_size, 
            self.player.z if self.proc_gen.view == 'z slice' else self.proc_gen.z_map[start_x + x, start_y + y])
            for x in range((ceil(RES[0] / self.cam.zoom_scale) // self.chunk_px_size) + 2) 
            for y in range((ceil(RES[1] / self.cam.zoom_scale) // self.chunk_px_size) + 2) 
        ]
      
    def get_chunk_img(self, chunk_x, chunk_y, chunk_z):
        img = pg.Surface((
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[0] - chunk_x)), 
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[1] - chunk_y))
        ), pg.SRCALPHA)

        tile_x, tile_y = chunk_x // TILE_SIZE, chunk_y // TILE_SIZE
        for x in range(img.width // TILE_SIZE):
            for y in range(img.height // TILE_SIZE):
                render_tile = False
                render_x, render_y = tile_x + x, tile_y + y
                if self.proc_gen.view in {'surface', 'elevation'}:
                    xyz = (render_x, render_y, int(self.proc_gen.z_map[render_x, render_y]))
                    if self.proc_gen.view == 'surface':
                        terrain_id = self.proc_gen.tile_map[xyz]
                        render_tile = terrain_id != self.proc_gen.tile_ids['air']
                    else:
                        if self.player.z not in self.proc_gen.z_dif_cache:
                            self.proc_gen.update_z_dif_cache(self.player.z)
                        
                        terrain_id = self.proc_gen.z_dif_cache[self.player.z][xyz[:2]]
                        render_tile = terrain_id != self.proc_gen.tile_ids['air']
                else:
                    terrain_id =  self.proc_gen.tile_map[render_x, render_y, self.player.z]
                    render_tile = terrain_id != self.proc_gen.tile_ids['air']
          
                if render_tile:
                    img.blit(self.assets.get_img(self.get_img_path(terrain_id)), (x * TILE_SIZE, y * TILE_SIZE))
        
        cache = self.get_cache()
        cache[(chunk_x, chunk_y, chunk_z)] = img
        return img
    
    def get_img_path(self, tile_id):
        img_name = self.proc_gen.id_tiles[tile_id]
        path = '../graphics/terrain/'
        for k in self.terrain_types:
            if img_name in self.terrain_types[k]:
                return path + k + f'/{img_name}.png'

    def get_cache(self):
        cache = None
        match self.proc_gen.view:
            case 'z slice': cache = self.z_slice_cache
            case 'elevation': cache = self.elev_view_cache
            case 'surface': cache = self.surface_view_cache

        return cache