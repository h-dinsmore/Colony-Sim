import pygame as pg

from mini_map import MiniMap
from info_ui import InfoUI
from settings import TILE_SIZE, MAP_TILE_SIZE, TILE_REACH_RADIUS

class UI:
    def __init__(self, cam, proc_gen, player, keyboard, mouse, chunk_renderer, weather, assets, clock, village):
        self.mouse = mouse
        self.assets = assets
        self.chunk_renderer = chunk_renderer
        self.proc_gen = proc_gen
        self.cam, self.old_zoom_scale = cam, cam.zoom_scale
        self.player = player

        self.mini_map = MiniMap(cam, proc_gen, player, keyboard, chunk_renderer, weather.sky.sky_rgb)

        self.info_ui = InfoUI(self.mini_map, player, keyboard, weather, assets.fonts['default'], clock, village)

        self.reachable_tile_surf = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.reachable_tile_surf.set_alpha(64)
       
    def highlight_tile_at_mouse(self, screen):
        x, y = self.mouse.tile_at
        z = self.player.z if self.chunk_renderer.view == 'z slice' else int(self.proc_gen.z_map[x, y])

        if self.chunk_renderer.view == 'elevation':
            if z not in self.proc_gen.z_dif_map:
                self.proc_gen.update_z_dif_map(z)
            tile_id = self.proc_gen.z_dif_map[z][x, y] 
        else:
            tile_id = self.proc_gen.tile_map[x, y, z]

        screen_xy = ((pg.Vector2(x, y) * TILE_SIZE) - self.cam.offset) * self.cam.zoom_scale
        if not (air_tile := tile_id == self.proc_gen.tile_ids['air']):
            img = self.assets.graphics['terrain'].files[self.proc_gen.id_tiles[tile_id]]
            screen.blit(
                img if self.cam.zoom_scale == 1.0 else pg.transform.scale(img, pg.Vector2(TILE_SIZE, TILE_SIZE) * self.cam.zoom_scale), 
                screen_xy,
                special_flags=pg.BLEND_RGB_ADD
            )
        self.render_reachable_tile_surf(screen, screen_xy, x, y, air_tile)

    def render_reachable_tile_surf(self, screen, screen_xy, x, y, air_tile):
        if self.old_zoom_scale != self.cam.zoom_scale:
            self.old_zoom_scale = self.cam.zoom_scale
            self.reachable_tile_surf = pg.transform.scale(self.reachable_tile_surf, pg.Vector2(TILE_SIZE, TILE_SIZE) * self.cam.zoom_scale)
        
        valid = abs(self.player.x - x) <= TILE_REACH_RADIUS and abs(self.player.y - y) <= TILE_REACH_RADIUS and \
            not air_tile
        if self.chunk_renderer.view != 'z slice': 
            valid &= abs(self.player.z - int(self.proc_gen.z_map[x, y])) <= 1
    
        self.reachable_tile_surf.fill('green' if valid else 'red')
        screen.blit(self.reachable_tile_surf, screen_xy)

    def spawn_item_sprite(self, tile_id, xy):
        tile_img = self.assets.get_tile_img

    def update(self, screen):
        self.mini_map.update(screen)
        self.info_ui.update(screen)
        self.highlight_tile_at_mouse(screen)