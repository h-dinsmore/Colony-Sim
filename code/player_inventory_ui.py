import pygame as pg

from settings import KEY_BINDINGS, TILE_SIZE
from os.path import join

class PlayerInventoryUI:
    def __init__(self, ui, player, mini_map, info_ui, assets, keyboard):
        self.ui = ui
        self.player = player
        self.mini_map = mini_map
        self.info_ui = info_ui
        self.assets = assets
        self.keyboard = keyboard

        self.num_cols = 8
        self.num_rows = player.max_slot_storage // self.num_cols
        self.box_len = info_ui.surf.width // self.num_cols
        self.outline_w = 1
        self.default_topleft = info_ui.rect.bottomleft
        self.topleft = self.default_topleft

        self.num_slots_filled = len(player.inv)
        self.item_names = list(player.inv)
        self.show = True
        self.open = False # show only the first row or the full inventory

        self.font = pg.font.Font(join('..', 'graphics', 'fonts', 'default.ttf'), size=8)
        self.line_color = self.mini_map.outline_color1
        self.inv_grid_open, self.inv_grid_closed = self.get_inv_grid_surfs()
        self.item_surfs, self.item_name_texts, self.item_amount_texts = {}, {}, {}

    def get_inv_grid_surfs(self):
        outline_offset = pg.Vector2(self.outline_w, self.outline_w)
        bg_surf = pg.Surface((pg.Vector2(self.num_cols, self.num_rows) * self.box_len) + outline_offset, pg.SRCALPHA)
        bg_surf.fill(self.mini_map.outline_color2)
        bg_surf.set_alpha(self.info_ui.alpha)

        for x in range(self.num_cols + 1):
            for y in range(self.num_rows + 1):
                vert_line_x, horiz_line_y = x * self.box_len, y * self.box_len
                pg.draw.line(bg_surf, self.line_color, (vert_line_x, 0), (vert_line_x, bg_surf.height), self.outline_w)
                pg.draw.line(bg_surf, self.line_color, (0, horiz_line_y), (bg_surf.width, horiz_line_y), self.outline_w)
       
        return bg_surf, bg_surf.subsurface((0,0), (bg_surf.width, self.box_len + outline_offset.y))

    def render(self, screen):
        surf = self.inv_grid_open if self.open else self.inv_grid_closed
        screen.blit(surf, surf.get_rect(topleft=self.topleft))
        for x in range(self.num_cols):
            for y in range(self.num_rows if self.open else 1):
                if (inv_idx := (self.num_cols * y) + x) < self.num_slots_filled:
                    if (item_name := self.item_names[inv_idx]) not in self.item_surfs:
                        self.item_surfs[item_name] = pg.transform.scale(self.assets.get_img(item_name), (TILE_SIZE * 2, TILE_SIZE * 2))
                    
                    item_rect = self.item_surfs[item_name].get_rect(center=box_outline.center)
                    screen.blit(self.item_surfs[item_name], item_rect)

                    if item_name not in self.item_name_texts:
                        self.item_name_texts[item_name] = self.font.render(item_name, self.ui.anti_alias, self.ui.font_color)
                    screen.blit(
                        self.item_name_texts[item_name], 
                        self.item_name_texts[item_name].get_rect(midtop=item_rect.midbottom + pg.Vector2(0, 1))
                    )

                    if (item_amount := str(self.player.inv[item_name]['amount'])) not in self.item_amount_texts:
                        self.item_amount_texts[item_name] = self.font.render(item_amount, self.ui.anti_alias, self.ui.font_color)
                    screen.blit(
                        self.item_amount_texts[item_name], 
                        self.item_amount_texts[item_name].get_rect(bottomright=box_bg_rect.bottomright - pg.Vector2(1, 1))
                    )

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