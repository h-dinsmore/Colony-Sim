import pygame as pg

from mini_map import MiniMap
from info_ui import InfoUI
from player_inventory_ui import PlayerInventoryUI
from settings import TILE_SIZE, MAP_TILE_SIZE, TILE_REACH_RADIUS

class UI:
    def __init__(self, cam, proc_gen, player, keyboard, mouse, chunk_renderer, weather, assets, clock, village):
        self.mouse = mouse
        self.assets = assets
        self.chunk_renderer = chunk_renderer
        self.proc_gen = proc_gen
        self.cam, self.old_zoom_scale = cam, cam.zoom_scale
        self.player = player

        self.anti_alias = False
        self.font_color = 'white'

        self.mini_map = MiniMap(self, cam, proc_gen, player, keyboard, chunk_renderer, weather.sky.sky_rgb)

        #self.info_ui = InfoUI(self, self.mini_map, player, keyboard, weather, assets.fonts['default'], clock, village)

        self.player_inv_ui = PlayerInventoryUI(self, player, self.mini_map, assets, keyboard, mouse)

        self.tile_holding_img = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.tile_holding_img.set_alpha(128)
        self.tile_holding_img_overlay = self.tile_holding_img.copy()
        self.tile_holding_img_overlay.set_alpha(self.tile_holding_img.get_alpha() // 2)
        self.old_item_holding = player.item_holding

        self.rect = pg.Rect((0,0), (self.mini_map.outline_rect2.width, self.mini_map.outline_rect2.height + self.player_inv_ui.rect.height))
       
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
        if tile_id != self.proc_gen.tile_ids['air']:
            img = self.assets.get_img(self.proc_gen.id_tiles[tile_id])
            screen.blit(
                img if self.cam.zoom_scale == 1.0 else pg.transform.scale(img, pg.Vector2(TILE_SIZE, TILE_SIZE) * self.cam.zoom_scale), 
                screen_xy, 
                special_flags=pg.BLEND_RGB_ADD
            )
        self.render_tile_holding_img(screen, screen_xy, x, y, z)

    def render_tile_holding_img(self, screen, screen_xy, x, y, z):
        if self.player.item_holding != self.old_item_holding:
            self.old_item_holding = self.player.item_holding
            if self.player.item_holding is not None:
                self.tile_holding_img = self.assets.get_img(self.player.item_holding) 

        if self.old_zoom_scale != self.cam.zoom_scale: 
            self.old_zoom_scale = self.cam.zoom_scale
            img_size_scaled = pg.Vector2(TILE_SIZE, TILE_SIZE) * self.cam.zoom_scale
            self.tile_holding_img = pg.transform.scale(self.tile_holding_img, img_size_scaled)
            self.tile_holding_img_overlay = pg.transform.scale(self.tile_holding_img_overlay, img_size_scaled)
            
        if self.player.item_holding is not None:
            screen.blit(self.tile_holding_img, screen_xy)

        self.tile_holding_img_overlay.fill('green' if self.player.check_valid_tile(x, y, z) else 'red')
        screen.blit(self.tile_holding_img_overlay, screen_xy)

    #def spawn_item_sprite(self, tile_id, xy):
        #tile_img = self.assets.get_tile_img

    def update_rect_height(self):
        mini_map_h = self.mini_map.outline_rect2.height if self.mini_map.show else 0
        player_inv_ui_h = self.player_inv_ui.rect.height if self.player_inv_ui.show else 0
        return mini_map_h + player_inv_ui_h
            
    def update(self, screen):
        self.mini_map.update(screen)
        #self.info_ui.update(screen)
        self.player_inv_ui.update(screen)
        if not self.rect.collidepoint(self.mouse.screen_pos):
            self.highlight_tile_at_mouse(screen)