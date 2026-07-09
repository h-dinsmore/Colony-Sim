import pygame as pg
import numpy as np
from random import randint, choice

from settings import MAP_TILE_SIZE, SOLID_TILES, TILE_SIZE, RES, KEY_BINDINGS, SCREEN_TILES

class MiniMap:
    def __init__(self, cam, proc_gen, player, keyboard, chunk_renderer, sky_rgb):
        self.cam = cam
        self.proc_gen = proc_gen
        self.player = player
        self.keyboard = keyboard
        self.chunk_renderer = chunk_renderer
        self.seen_tiles = np.full(MAP_TILE_SIZE, False, dtype=bool) 
        self.non_tile_rgbs = {
            'air': sky_rgb, 
            'water': (30, 136, 229),
            'lava': (255, 48, 0),
            'honey': (250, 213, 53)
        }

        self.tiles_across = 64
        self.tile_size = 4
        self.px_across = self.tiles_across * self.tile_size
        self.update_radius = 2
        
        self.chunks_across = 4
        self.chunk_tiles_across = self.tiles_across // self.chunks_across
        self.chunk_px_size = self.chunk_tiles_across * self.tile_size
        self.max_chunk_start_x = (MAP_TILE_SIZE[0] - 1) - self.chunk_tiles_across
        self.max_chunk_start_y = (MAP_TILE_SIZE[1] - 1) - self.chunk_tiles_across

        self.chunk_img_cache = {k: {} for k in self.chunk_renderer.view_types}
        self.chunk_tiles_seen = {k: {} for k in self.chunk_renderer.view_types} 

        self.padding = 4
        self.topleft = pg.Vector2(self.padding, self.padding)
        self.img = pg.Surface((self.px_across, self.px_across))
        self.outline_w = 2
        self.outline_rect = pg.Rect(
            self.topleft - pg.Vector2(self.outline_w, self.outline_w), 
            self.img.get_size() + (pg.Vector2(self.outline_w, self.outline_w) * 2)
        )
        self.outline_rect2 = pg.Rect(
            self.outline_rect.topleft - pg.Vector2(self.outline_w, self.outline_w), 
            self.outline_rect.size + (pg.Vector2(self.outline_w, self.outline_w) * 2)
        )
        self.outline_color1, self.outline_color2 = 'darkorchid', 'darkorchid4'

        self.prev_cam_offset = cam.offset.copy()
        self.prev_view = chunk_renderer.view
        self.prev_z = self.player.z
        self.render = True

    def render_tiles(self, screen): 
        cam_x, cam_y = self.cam.offset
        z_slice_view = self.chunk_renderer.view == 'z slice'
        if self.check_display_update():
            start_tile_x = int(cam_x) // self.chunk_tiles_across
            start_tile_y = int(cam_y) // self.chunk_tiles_across
            for x in range(self.chunks_across):
                for y in range(self.chunks_across):
                    chunk_start_x = min(self.max_chunk_start_x, start_tile_x + (x * self.chunk_tiles_across))
                    chunk_start_y = min(self.max_chunk_start_y, start_tile_y + (y * self.chunk_tiles_across))
                    chunk_start_z = self.player.z if z_slice_view else int(self.proc_gen.z_map[chunk_start_x, chunk_start_y])
                    chunk_xyz = (chunk_start_x, chunk_start_y, chunk_start_z)

                    chunk_end_x = chunk_start_x + self.chunk_tiles_across
                    chunk_end_y = chunk_start_y + self.chunk_tiles_across

                    x_idxs = np.arange(chunk_start_x, chunk_end_x).astype(np.int8)[:, None]
                    y_idxs = np.arange(chunk_start_y, chunk_end_y).astype(np.int8)[None, :]
                    cur_seen_tiles = self.seen_tiles[
                        x_idxs, y_idxs, self.player.z if z_slice_view else self.proc_gen.z_map[x_idxs, y_idxs]
                    ]
                    
                    if (prev_seen_tiles := self.chunk_tiles_seen[self.chunk_renderer.view].get(chunk_xyz)) is None:
                        self.chunk_img_cache[self.chunk_renderer.view][chunk_xyz] = self.get_chunk_img(*chunk_xyz[:2])
                    
                    elif not np.array_equal(prev_seen_tiles, cur_seen_tiles):
                        self.chunk_img_cache[self.chunk_renderer.view][chunk_xyz] = self.update_chunk_img(
                            *chunk_xyz, prev_seen_tiles, cur_seen_tiles
                        )

                    self.chunk_tiles_seen[self.chunk_renderer.view][chunk_xyz] = cur_seen_tiles
                    
                    self.img.blit(
                        self.chunk_img_cache[self.chunk_renderer.view][chunk_xyz], 
                        (x * self.chunk_px_size, y * self.chunk_px_size)
                    )
    
        screen.blit(self.img, self.topleft)

    def check_display_update(self):
        update = False

        new_cam_offset = self.cam.offset != self.prev_cam_offset
        new_view = self.prev_view != self.chunk_renderer.view
        tile_x, tile_y = self.player.rect.x // TILE_SIZE, self.player.rect.y // TILE_SIZE
        new_seen_tile = self.seen_tiles[tile_x, tile_y, self.player.z] == False
        new_z = self.prev_z != self.player.z
        if new_cam_offset or new_view or new_seen_tile or new_z:
            if new_cam_offset:
                self.prev_cam_offset = self.cam.offset.copy()
                update = True

            if new_view:
                self.prev_view = self.chunk_renderer.view
                update = True
            
            if new_seen_tile:
                self.update_seen_tiles(tile_x, tile_y)
                update = True

            if new_z:
                self.prev_z = self.player.z
                if not update:
                    update = self.chunk_renderer.view == 'z slice'

        return update

    def update_seen_tiles(self, tile_x, tile_y):
        min_x = max(0, tile_x - self.update_radius)
        max_x = min(MAP_TILE_SIZE[0] - 1, tile_x + self.update_radius)

        min_y = max(0, tile_y - self.update_radius)
        max_y = min(MAP_TILE_SIZE[1] - 1, tile_y + self.update_radius)

        if self.chunk_renderer.view == 'z slice':
            z = self.player.z
        else:
            z = self.proc_gen.z_map[min_x:max_x, min_y:max_y] 

        self.seen_tiles[min_x:max_x, min_y:max_y, z] = True

    def get_chunk_img(self, chunk_x, chunk_y):
        img = pg.Surface((self.chunk_px_size, self.chunk_px_size))
        tile = pg.Surface((self.tile_size, self.tile_size))
        for x in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[0] - 1 - chunk_x)):
            for y in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[1] - 1 - chunk_y)):
                tile_x, tile_y = chunk_x + x, chunk_y + y
                tile_z = self.player.z if self.chunk_renderer.view == 'z slice' else self.proc_gen.z_map[tile_x, tile_y]
                if self.seen_tiles[tile_x, tile_y, tile_z]:
                    if color := self.get_tile_color(self.proc_gen.id_tiles[self.proc_gen.tile_map[tile_x, tile_y, tile_z]]):
                        tile.fill(color)
                        img.blit(tile, (x * self.tile_size, y * self.tile_size))
        return img
    
    def update_chunk_img(self, chunk_x, chunk_y, chunk_z, prev_seen_tiles, cur_seen_tiles):
        img = self.chunk_img_cache[self.chunk_renderer.view][(chunk_x, chunk_y, chunk_z)]
        tile = pg.Surface((self.tile_size, self.tile_size))
        for col, row in np.argwhere(prev_seen_tiles != cur_seen_tiles): 
            tile_x, tile_y = chunk_x + col, chunk_y + row
            tile_z = self.player.z if self.chunk_renderer.view == 'z slice' else self.proc_gen.z_map[tile_x, tile_y]
            if color := self.get_tile_color(self.proc_gen.id_tiles[self.proc_gen.tile_map[tile_x, tile_y, tile_z]]):
                tile.fill(color) 
                img.blit(tile, (col * self.tile_size, row * self.tile_size))
        return img
 
    def get_tile_color(self, name):
        if name in SOLID_TILES:
            return SOLID_TILES[name].get('minimap rgb')
        
        if name in self.non_tile_rgbs:
            return self.non_tile_rgbs[name]
        
        return (255, 0, 0)

    def update(self, screen):
        if self.keyboard.pressed_keys[KEY_BINDINGS['mini map view']]:
            self.render = not self.render

        if self.render:
            self.render_tiles(screen)
            pg.draw.rect(screen, self.outline_color1, self.outline_rect, self.outline_w)
            pg.draw.rect(screen, self.outline_color2, self.outline_rect2, self.outline_w)