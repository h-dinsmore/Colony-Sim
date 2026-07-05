import pygame as pg
from math import ceil

from settings import *

class ChunkRenderer:
    def __init__(self, world_surf, proc_gen, assets, cam, player, keyboard):
        self.world_surf = world_surf
        self.proc_gen = proc_gen
        self.assets = assets
        self.cam, self.prev_cam_offset = cam, pg.Vector2()
        self.player = player
        self.keyboard = keyboard
        
        self.chunk_tile_size = 32
        self.chunk_px_size = self.chunk_tile_size * TILE_SIZE
        self.visible_chunks = []
        self.max_chunk_xy = MAP_PX_SIZE[0] // self.chunk_px_size, MAP_PX_SIZE[1] // self.chunk_px_size

        self.view_types = ('elevation', 'surface', 'z slice')
        self.view = 'surface'
        self.prev_z, self.prev_view = player.z, self.view
        self.img_cache = {k: {} for k in self.view_types}
        self.img_path_cache = {}
        
        self.terrain_types = {
            'solid tiles': SOLID_TILES.keys(), 
            'surface terrain': SURFACE_TERRAIN,
            'elevations': ELEVATIONS, 
            'trees': TREES, 
            'liquids': LIQUIDS
        }

    def render(self):
        new_cam_offset = self.cam.offset != self.prev_cam_offset
        new_z_lvl = self.player.z != self.prev_z
        new_view = self.prev_view != self.view
        if new_cam_offset or new_z_lvl or new_view:
            self.visible_chunks = self.get_visible_chunks()

            if new_cam_offset:
                self.prev_cam_offset = self.cam.offset.copy()

            if new_z_lvl:
                self.prev_z = self.player.z
                self.proc_gen.update_z_dif_map(self.player.z)

            if new_view:
                self.prev_view = self.view
        
        cache = self.img_cache[self.view]
        for xyz in self.visible_chunks:
            self.world_surf.blit(cache[xyz] if xyz in cache else self.get_chunk_img(*xyz), xyz[:2])
        
    def get_visible_chunks(self):
        cam_x, cam_y = self.cam.offset // self.chunk_px_size
        start_x = max(0, min(int(cam_x), self.max_chunk_xy[0]))
        start_y = max(0, min(int(cam_y), self.max_chunk_xy[1]))
        return [
            ((start_x + x) * self.chunk_px_size, (start_y + y) * self.chunk_px_size, 
            self.player.z if self.view != 'surface' else int(self.proc_gen.z_map[start_x + x, start_y + y]))
            for x in range((ceil(RES[0] / self.cam.zoom_scale) // self.chunk_px_size) + 2) 
            for y in range((ceil(RES[1] / self.cam.zoom_scale) // self.chunk_px_size) + 2) 
        ]
      
    def get_chunk_img(self, chunk_x, chunk_y, chunk_z):
        img = pg.Surface((
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[0] - chunk_x)), 
            max(0, min(self.chunk_px_size, MAP_PX_SIZE[1] - chunk_y))
        ), pg.SRCALPHA)

        if self.view == 'elevation' and self.player.z not in self.proc_gen.z_dif_map:
            self.proc_gen.update_z_dif_map(self.player.z)
        
        tile_x, tile_y = chunk_x // TILE_SIZE, chunk_y // TILE_SIZE
        for x in range(img.width // TILE_SIZE):
            for y in range(img.height // TILE_SIZE):
                if tile_id := self.get_tile_id(tile_x + x, tile_y + y):
                    img.blit(self.assets.get_img(self.get_img_path(tile_id)), (x * TILE_SIZE, y * TILE_SIZE))
        
        self.img_cache[self.view][(chunk_x, chunk_y, chunk_z)] = img
        return img

    def get_tile_id(self, x, y):
        tile_id = None
        if self.view == 'z slice':
            tile_id = self.proc_gen.tile_map[x, y, self.player.z]
        else:
            tile_z = int(self.proc_gen.z_map[x, y])
            if self.view == 'surface' or self.player.z == tile_z:
                tile_id = self.proc_gen.tile_map[x, y, tile_z]
            else:
                tile_id = self.proc_gen.z_dif_map[self.player.z][x, y]
        
        if tile_id != self.proc_gen.tile_ids['air']:
            return tile_id
        return None
    
    def get_img_path(self, tile_id):
        if (img_name := self.proc_gen.id_tiles[tile_id]) in self.img_path_cache:
            return self.img_path_cache[img_name]

        path = '../graphics/terrain/'
        for k in self.terrain_types:
            if img_name in self.terrain_types[k]:
                full_path = path + k + f'/{img_name}.png'
                self.img_path_cache[img_name] = full_path
                return full_path

    def get_cache(self):
        match self.view:
            case 'z slice': return self.z_slice_cache
            case 'elevation': return self.elev_view_cache
            case 'surface': return self.surface_view_cache

    def update(self):
        for view_type in self.view_types:
            if self.keyboard.pressed_keys[KEY_BINDINGS[f'{view_type} view']]:
                self.view = view_type

        self.render()