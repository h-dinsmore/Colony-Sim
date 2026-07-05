import pygame as pg
import numpy as np
from random import randint, choice

from settings import MAP_TILE_SIZE, SOLID_TILES, TILE_SIZE, RES, KEY_BINDINGS, SCREEN_TILES

class MiniMap:
    def __init__(self, cam, screen, proc_gen, player, keyboard, sky_rgb):
        self.cam = cam
        self.screen = screen
        self.proc_gen = proc_gen
        self.player = player
        self.keyboard = keyboard

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
        self.update_radius = RES
        
        self.chunks_across = 4
        self.chunk_tiles_across = self.tiles_across // self.chunks_across
        self.chunk_px_size = self.chunk_tiles_across * self.tile_size
        self.chunk_img_cache = {}
        self.chunk_tiles = {} 

        self.padding = 4
        self.topleft = pg.Vector2(self.padding, self.padding)
        self.img = pg.Surface((self.px_across, self.px_across))
        self.outline_w = 2
        self.outline_rect = pg.Rect(
            self.topleft - pg.Vector2(self.outline_w, self.outline_w), 
            self.img.get_size() + pg.Vector2(self.outline_w * 2, self.outline_w * 2)
        )
        self.outline_rect2 = pg.Rect(
            self.outline_rect.topleft - pg.Vector2(self.outline_w, self.outline_w), 
            self.outline_rect.size + pg.Vector2(self.outline_w * 2, self.outline_w * 2)
        )
        self.prev_cam_offset, self.prev_z = cam.offset.copy(), player.z
        self.render = True

    def render_tiles(self, screen): 
        cam_x, cam_y = self.cam.offset
        if self.check_update():
            chunk_start_x = (int(cam_x) // self.chunk_tiles_across) * self.chunk_tiles_across
            chunk_start_y = (int(cam_y) // self.chunk_tiles_across) * self.chunk_tiles_across
            tile_x, tile_y = min(MAP_TILE_SIZE[0] - SCREEN_TILES[0], chunk_start_x // TILE_SIZE), min(MAP_TILE_SIZE[1] - SCREEN_TILES[1], chunk_start_x // TILE_SIZE)

            for x in range(self.chunk_tiles_across):
                for y in range(self.chunk_tiles_across):
                    chunk_x, chunk_y = tile_x + (x * self.chunk_tiles_across), tile_y + (y * self.chunk_tiles_across)
                    max_x = min(chunk_x + self.chunk_tiles_across, MAP_TILE_SIZE[0] - 1)
                    max_y = min(chunk_y + self.chunk_tiles_across, MAP_TILE_SIZE[1] - 1)

                    if (prev_seen := self.chunk_tiles.get((chunk_x, chunk_y, self.player.z))) is None:
                        self.chunk_img_cache[(chunk_x, chunk_y, self.player.z)] = self.get_chunk_img(chunk_x, chunk_y)
                        self.chunk_tiles[(chunk_x, chunk_y, self.player.z)] = self.seen_tiles[chunk_x:max_x, chunk_y:max_y, self.player.z]
                    else:
                        cur_seen = self.seen_tiles[chunk_x:max_x, chunk_y:max_y, self.player.z]
                        if not np.array_equal(prev_seen, cur_seen):
                            self.chunk_img_cache[(chunk_x, chunk_y, self.player.z)] = self.update_chunk_img(chunk_x, chunk_y, prev_seen, cur_seen)
                            self.chunk_tiles[(chunk_x, chunk_y, self.player.z)] = cur_seen
                    
                    self.img.blit(self.chunk_img_cache[(chunk_x, chunk_y, self.player.z)], (x * self.chunk_px_size, y * self.chunk_px_size))

        screen.blit(self.img, self.topleft)

    def check_update(self):
        new_cam_offset = self.cam.offset != self.prev_cam_offset
        new_z = self.player.z != self.prev_z
        if new_cam_offset or new_z:
            self.update_seen_tiles()

            if new_cam_offset:
                self.old_cam_offset = self.cam.offset.copy()

            if new_z:
                self.prev_z = self.player.z

            return True
        return False

    def update_seen_tiles(self):
        offset_x, offset_y = self.cam.center_xy // TILE_SIZE # using the center instead of the topleft offset to update the tiles around the player
        offset_x, offset_y = int(offset_x), int(offset_y) # was still a float bc center is a vector2
        self.seen_tiles[
            max(0, offset_x - self.update_radius[0]):min(MAP_TILE_SIZE[0], offset_x + self.update_radius[0]),
            max(0, offset_y - self.update_radius[1]):min(MAP_TILE_SIZE[1], offset_y + self.update_radius[1]),
            self.player.z
        ] = True

    def get_chunk_img(self, chunk_x, chunk_y):
        img = pg.Surface((self.chunk_px_size, self.chunk_px_size))
        tile = pg.Surface((self.tile_size, self.tile_size))
        for x in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[0] - 1 - chunk_x)):
            for y in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[1] - 1 - chunk_y)):
                tile_xyz = chunk_x + x, chunk_y + y, self.player.z
                if self.seen_tiles[tile_xyz]:
                    if color := self.get_tile_color(self.proc_gen.id_tiles[self.proc_gen.tile_map[tile_xyz]]):
                        tile.fill(color)
                        img.blit(tile, (x * self.tile_size, y * self.tile_size))
        return img
    
    def update_chunk_img(self, chunk_x, chunk_y, prev_seen, cur_seen):
        img = self.chunk_img_cache[(chunk_x, chunk_y, self.player.z)]
        tile = pg.Surface((self.tile_size, self.tile_size))
        for col, row in np.argwhere(prev_seen != cur_seen): 
            tile_xyz = chunk_x + col, chunk_y + row, self.player.z
            if color := self.get_tile_color(self.proc_gen.id_tiles[self.proc_gen.tile_map[tile_xyz]]):
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
            pg.draw.rect(screen, 'darkorchid', self.outline_rect, self.outline_w)
            pg.draw.rect(screen, 'darkorchid4', self.outline_rect2, self.outline_w)