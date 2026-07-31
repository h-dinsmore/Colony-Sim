import pygame as pg
import numpy as np
from random import randint, choice

from settings import MAP_TILE_SIZE, SOLID_TILES, TILE_SIZE, RES, KEY_BINDINGS, SCREEN_TILES, SURFACE_TERRAIN, LIQUIDS

class MiniMap:
    def __init__(self, ui, cam, proc_gen, player, keyboard, chunk_renderer, sky_rgb):
        self.ui = ui
        self.cam = cam
        self.proc_gen = proc_gen
        self.player = player
        self.keyboard = keyboard
        self.chunk_renderer = chunk_renderer
        self.air_rgb = sky_rgb

        self.seen_tiles = np.full(MAP_TILE_SIZE, False, dtype=bool) 
      
        self.tiles_across = 64
        self.tile_size = 4
        self.px_across = self.tiles_across * self.tile_size
        self.update_radius = 2
        
        self.chunks_across = 4
        self.chunk_tiles_across = self.tiles_across // self.chunks_across
        self.chunk_px_size = self.chunk_tiles_across * self.tile_size
        self.max_start_tile_x = MAP_TILE_SIZE[0] - self.tiles_across
        self.max_start_tile_y = MAP_TILE_SIZE[1] - self.tiles_across

        self.chunk_img = pg.Surface((self.chunk_px_size, self.chunk_px_size))
        self.chunk_tile = pg.Surface((self.tile_size, self.tile_size))
        self.chunk_img_cache = {k: {} for k in self.chunk_renderer.view_types}
        self.chunk_tiles_seen = {k: {} for k in self.chunk_renderer.view_types} 

        self.padding = 4
        self.topleft = pg.Vector2(self.padding)
        self.img = pg.Surface((self.px_across, self.px_across))
        self.outline_w = 2
        self.outline_rect = pg.Rect(
            self.topleft - pg.Vector2(self.outline_w), 
            self.img.get_size() + (pg.Vector2(self.outline_w) * 2)
        )
        self.outline_rect2 = pg.Rect(
            self.outline_rect.topleft - pg.Vector2(self.outline_w), 
            self.outline_rect.size + (pg.Vector2(self.outline_w) * 2)
        )
        self.outline_color1, self.outline_color2 = 'purple4', 'indigo'
        self.num_outlines = 2

        self.prev_cam_offset = cam.offset.copy()
        self.prev_view = chunk_renderer.view
        self.prev_z = self.player.z
        self.show = True

    def render_tiles(self, screen): 
        if self.check_display_update():
            player_tile_x, player_tile_y = self.player.tile_xy
            map_start_x = max(0, min(int(player_tile_x) - (self.tiles_across // 2), self.max_start_tile_x))
            map_start_y = max(0, min(int(player_tile_y) - (self.tiles_across // 2), self.max_start_tile_y))
            chunk_start_x = (map_start_x // self.chunk_tiles_across) * self.chunk_tiles_across
            chunk_start_y = (map_start_y // self.chunk_tiles_across) * self.chunk_tiles_across
            
            z_slice_view = self.chunk_renderer.view == 'z slice'
            for x in range(self.chunks_across):
                for y in range(self.chunks_across):
                    chunk_x, chunk_y = chunk_start_x + (x * self.chunk_tiles_across), chunk_start_y + (y * self.chunk_tiles_across)
                    chunk_key = (chunk_x, chunk_y, int(self.proc_gen.z_map[chunk_x, chunk_y])) # using the z_map even for the z slice view to have a consistent cache index for the tile

                    chunk_tiles_x = np.arange(chunk_x, chunk_x + self.chunk_tiles_across).astype(np.int8)[:, None]
                    chunk_tiles_y = np.arange(chunk_y, chunk_y + self.chunk_tiles_across).astype(np.int8)[None, :]
                    cur_seen_tiles = self.seen_tiles[chunk_tiles_x, chunk_tiles_y, self.player.z if z_slice_view else self.proc_gen.z_map[chunk_tiles_x, chunk_tiles_y]]
                    
                    if (prev_seen_tiles := self.chunk_tiles_seen[self.chunk_renderer.view].get(chunk_key)) is None:
                        self.chunk_img_cache[self.chunk_renderer.view][chunk_key] = self.get_chunk_img(*chunk_key[:2])
                    
                    elif not np.array_equal(prev_seen_tiles, cur_seen_tiles):
                        self.chunk_img_cache[self.chunk_renderer.view][chunk_key] = self.update_chunk_img(*chunk_key, prev_seen_tiles, cur_seen_tiles)

                    self.chunk_tiles_seen[self.chunk_renderer.view][chunk_key] = cur_seen_tiles
                    self.img.blit(self.chunk_img_cache[self.chunk_renderer.view][chunk_key], (x * self.chunk_px_size, y * self.chunk_px_size))
                    
        screen.blit(self.img, self.topleft)

    def check_display_update(self):
        update = False
        new_cam_offset = self.cam.offset != self.prev_cam_offset
        new_view = self.prev_view != self.chunk_renderer.view
        new_seen_tile = self.seen_tiles[*self.player.tile_xy, self.player.z] == False
        new_z = self.prev_z != self.player.z
        if new_cam_offset or new_view or new_seen_tile or new_z:
            if new_cam_offset:
                self.prev_cam_offset = self.cam.offset.copy()
                update = True

            if new_view:
                self.prev_view = self.chunk_renderer.view
                update = True
            
            if new_seen_tile:
                self.update_seen_tiles(*self.player.tile_xy)
                update = True

            if new_z:
                self.prev_z = self.player.z
                if not update:
                    update = self.chunk_renderer.view == 'z slice'
        return update

    def update_seen_tiles(self, tile_x, tile_y):
        min_x = max(0, tile_x - self.update_radius)
        max_x = min(MAP_TILE_SIZE[0], tile_x + self.update_radius)

        min_y = max(0, tile_y - self.update_radius)
        max_y = min(MAP_TILE_SIZE[1], tile_y + self.update_radius)

        if self.chunk_renderer.view == 'z slice':
            z = self.player.z
        else:
            z = self.proc_gen.z_map[min_x:max_x, min_y:max_y] 

        self.seen_tiles[min_x:max_x, min_y:max_y, z] = True

    def get_chunk_img(self, chunk_x, chunk_y):
        img = self.chunk_img.copy()
        tile = self.chunk_tile.copy()
        for x in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[0] - chunk_x)):
            for y in range(min(self.chunk_tiles_across, MAP_TILE_SIZE[1] - chunk_y)):
                tile_x, tile_y = chunk_x + x, chunk_y + y
                if self.seen_tiles[tile_x, tile_y, self.proc_gen.z_map[tile_x, tile_y]]:
                    if color := self.get_tile_color(self.chunk_renderer.get_tile_name(tile_x, tile_y)):
                        tile.fill(color)
                        img.blit(tile, (x * self.tile_size, y * self.tile_size))
        return img
    
    def update_chunk_img(self, chunk_x, chunk_y, chunk_z, prev_seen_tiles, cur_seen_tiles):
        img = self.chunk_img_cache[self.chunk_renderer.view][(chunk_x, chunk_y, chunk_z)]
        tile = self.chunk_tile.copy()
        for col, row in np.argwhere(prev_seen_tiles != cur_seen_tiles): 
            if color := self.get_tile_color(self.chunk_renderer.get_tile_name(chunk_x + col, chunk_y + row)):
                tile.fill(color) 
                img.blit(tile, (col * self.tile_size, row * self.tile_size))
        return img

    def update_tile_in_chunk(self, x, y, z, new_tile_name):
        chunk_x, chunk_y = (x // self.chunk_tiles_across) * self.chunk_tiles_across, (y // self.chunk_tiles_across) * self.chunk_tiles_across
        chunk_z = z if (chunk_x, chunk_y) == (x, y) else self.proc_gen.z_map[chunk_x, chunk_y]
        px_xy_in_chunk = (pg.Vector2(x, y) - pg.Vector2(chunk_x, chunk_y)) * self.tile_size

        tile_surf = self.chunk_tile.copy()
        tile_surf.fill(self.get_tile_color(new_tile_name))
        chunk_key = (chunk_x, chunk_y, self.proc_gen.z_map[chunk_x, chunk_y])
        for view in (v for v in self.chunk_renderer.view_types if chunk_key in self.chunk_img_cache[v]):
            self.chunk_img_cache[view][chunk_key].blit(tile_surf, px_xy_in_chunk)

    def get_tile_color(self, tile_name):
        if tile_name == 'air':
            return self.air_rgb

        tile_category = None
        for category in (SOLID_TILES, SURFACE_TERRAIN, LIQUIDS):
            if tile_name in category:
                tile_category = category
                break
        
        if (rgb := tile_category[tile_name].get('minimap rgb')) is not None:
            return rgb
        return (0, 255, 0)

    def update_chunk_img_cache_key(self, tile_x, tile_y, old_z, new_z):
        chunk_x, chunk_y = (tile_x // self.chunk_tiles_across) * self.chunk_tiles_across, (tile_y // self.chunk_tiles_across) * self.chunk_tiles_across
        for view in (v for v in self.chunk_renderer.view_types if (chunk_x, chunk_y, old_z) in self.chunk_img_cache[v]):
            img = self.chunk_img_cache[view][(chunk_x, chunk_y, old_z)]
            del self.chunk_img_cache[view][(chunk_x, chunk_y, old_z)]
            self.chunk_img_cache[view][(chunk_x, chunk_y, new_z)] = img

    def update(self, screen):
        if self.keyboard.pressed_keys[KEY_BINDINGS['mini map view']]:
            self.show = not self.show
            self.ui.rect.height = self.ui.update_rect_height()
            self.ui.player_inv_ui.update_topleft()

        if self.show:
            self.render_tiles(screen)
            pg.draw.rect(screen, self.outline_color1, self.outline_rect, self.outline_w)
            pg.draw.rect(screen, self.outline_color2, self.outline_rect2, self.outline_w)