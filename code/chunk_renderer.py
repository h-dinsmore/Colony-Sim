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

        self.chunk_tile_size = 32
        self.chunk_px_size = self.chunk_tile_size * TILE_SIZE
        self.visible_chunks = []
        self.max_chunk_xy = MAP_PX_SIZE[0] // self.chunk_px_size, MAP_PX_SIZE[1] // self.chunk_px_size

        self.view_types = ('elevation', 'surface', 'z slice')
        self.view = 'surface'
        self.prev_z, self.prev_view = None, None
        self.img_cache = {k: {} for k in self.view_types}

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
                if self.player.z not in self.proc_gen.z_dif_map:
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
        z_slice_view = self.view == 'z slice'
        return [
            ((start_x + x) * self.chunk_px_size, (start_y + y) * self.chunk_px_size, 
            self.player.z if z_slice_view else int(self.proc_gen.z_map[start_x + x, start_y + y]))
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

        img_folder = self.assets.graphics['terrain'].files
        tile_x, tile_y = chunk_x // TILE_SIZE, chunk_y // TILE_SIZE
        for x in range(img.width // TILE_SIZE):
            for y in range(img.height // TILE_SIZE):
                if (tile_name := self.get_tile_name(tile_x + x, tile_y + y)) != 'air':
                    img.blit(img_folder[tile_name], (x * TILE_SIZE, y * TILE_SIZE))
        
        self.img_cache[self.view][(chunk_x, chunk_y, chunk_z)] = img
        return img

    def update_tile_in_chunk(self, tile_x, tile_y, hardness, tile_name):
        chunk_tile_x = tile_x // self.chunk_tile_size
        chunk_tile_y = tile_y // self.chunk_tile_size

        chunk_px_x = ((tile_x * TILE_SIZE) // self.chunk_px_size) * self.chunk_px_size
        chunk_px_y = ((tile_y * TILE_SIZE) // self.chunk_px_size) * self.chunk_px_size

        tile_xy_in_chunk = (pg.Vector2(tile_x, tile_y) * TILE_SIZE) - pg.Vector2(chunk_px_x, chunk_px_y)
        chunk_key = (chunk_px_x, chunk_px_y, int(self.proc_gen.z_map[chunk_tile_x, chunk_tile_y]))
        
        solid_tile = hardness > 0 and tile_name in SOLID_TILES
        for view in [v for v in self.view_types if chunk_key in self.img_cache[v]]:
            self.img_cache[view][chunk_key].blit(
                self.get_tile_below_img(view, tile_name, hardness, solid_tile, tile_x, tile_y), 
                tile_xy_in_chunk
            )

    def get_tile_z_idx(self, tile_x, tile_y):
        match self.view:
            case 'surface': 
                return self.proc_gen.z_map[tile_x, tile_y]
            case 'z slice': 
                return self.player.z
            case 'elevation': 
                return self.proc_gen.z_dif_map[self.player.z][tile_x, tile_y]

    def get_tile_below_img(self, view, tile_name, hardness, solid_tile, tile_x, tile_y):
        match view:
            case 'z slice':
                tile_img = self.get_air_tile_img()

            case 'surface':
                if self.proc_gen.z_map[tile_x, tile_y] == 0:
                    tile_img = self.get_air_tile_img()
                else:
                    if tile_name != 'air':
                        tile_img = self.assets.graphics['terrain'].files[tile_name].copy() 
                        if solid_tile: # if hardness is 0 then the map was updated before this function was called and the tile below it will show
                            tile_img.set_alpha(int(255 * (hardness / SOLID_TILES[tile_name]['hardness'])))
                    else:
                        tile_img = self.get_air_tile_img()

            case 'elevation':
                tile_img = self.assets.graphics['terrain'].files[tile_name].copy()
                if solid_tile:
                    tile_img.set_alpha(int(255 * (hardness / SOLID_TILES[tile_name]['hardness'])))
        return tile_img
    
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

    def update(self):
        for view_type in self.view_types:
            if self.keyboard.pressed_keys[KEY_BINDINGS[f'{view_type} view']]:
                self.view = view_type

        self.render()