import pygame as pg

from settings import KEY_BINDINGS

class PlayerInventoryUI:
    def __init__(self, ui, player, mini_map, info_ui, assets, keyboard):
        self.ui = ui
        self.player = player
        self.mini_map = mini_map
        self.info_ui = info_ui
        self.assets = assets
        self.keyboard = keyboard

        self.num_cols = 8
        self.num_rows = player.max_inv_items // self.num_cols
        self.box_len = info_ui.surf.width // self.num_cols
        self.outline_w = 1
        self.default_topleft = info_ui.rect.bottomleft
        self.topleft = self.default_topleft

        self.show = True
        self.open = False # show only the first row or the full inventory
        self.font = self.assets.fonts['default']

    def render(self, screen):
        num_slots_filled = len(self.player.inv)
        inv_keys = list(self.player.inv.keys())
        for x in range(self.num_cols):
            for y in range(self.num_rows if self.open else 1):
                box_outline = pg.Rect(
                    self.topleft + pg.Vector2(x * self.box_len, y * self.box_len), 
                    pg.Vector2(self.box_len, self.box_len) + (pg.Vector2(self.outline_w, self.outline_w) * 2)
                )
                
                box_bg_surf = pg.Surface(box_outline.size - (pg.Vector2(self.outline_w, self.outline_w) * 2))
                box_bg_surf.fill(self.mini_map.outline_color2)
                box_bg_surf.set_alpha(self.info_ui.alpha)
                box_bg_rect = box_bg_surf.get_rect(topleft=box_outline.topleft + pg.Vector2(self.outline_w, self.outline_w))
                screen.blit(box_bg_surf, box_bg_rect)
                pg.draw.rect(screen, 'black', box_outline, 1)

                if (inv_idx := (self.num_cols * y) + x) < num_slots_filled:
                    item_name = inv_keys[inv_idx]

                    item_surf = self.assets.get_img(item_name)
                    item_rect =  item_surf.get_rect(center=box_outline.center)
                    screen.blit(item_surf, item_rect)

                    item_name_surf = self.font.render(item_name, self.ui.anti_alias, self.ui.font_color)
                    screen.blit(item_name_surf, item_name_surf.get_rect(midtop=item_rect.midbottom + pg.Vector2(0, 1)))

                    item_amount_surf = self.font.render(str(self.player.inv[item_name]['amount']), self.ui.anti_alias, self.ui.font_color)
                    screen.blit(item_amount_surf, item_amount_surf.get_rect(bottomright=box_bg_rect.bottomright - pg.Vector2(1, 1)))

    def check_keyboard_input(self):
        if self.keyboard.pressed_keys[KEY_BINDINGS['player inv view']]:
            self.show = not self.show
        
        if self.keyboard.pressed_keys[KEY_BINDINGS['open/close player inv']]:
            self.open = not self.open
            self.topleft = self.default_topleft if not self.open else self.info_ui.rect.bottomleft

    def update(self, screen):
        self.check_keyboard_input()
        if self.show:
            self.render(screen)