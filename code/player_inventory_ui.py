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

        self.num_slots_filled = len(player.inv)
        self.item_names = list(player.inv)
        self.item_surfs = {}
        self.show = True
        self.open = False # show only the first row or the full inventory
        self.old_topleft = None
        
        self.txt_font = pg.font.Font(join('..', 'graphics', 'fonts', 'default.ttf'), size=10)
        self.num_font = pg.font.Font(join('..', 'graphics', 'fonts', 'default.ttf'), size=8)
        self.line_color = self.mini_map.outline_color1

        self.surf_open, self.surf_closed = self.get_surfs()
        self.rect_open = self.surf_open.get_rect()
        self.rect_closed = self.surf_closed.get_rect()
        self.rect = self.rect_closed

    @property
    def topleft(self):
        if self.info_ui.show:
            topleft = self.info_ui.rect.bottomleft
        elif self.mini_map.show:
            topleft = self.mini_map.rect.bottomleft
        else:
            topleft = pg.Vector2()

        if topleft != self.old_topleft:
            self.old_topleft = topleft
            self.rect_open.topleft = topleft
            self.rect_closed.topleft = topleft
        
        return topleft

    def get_surfs(self):
        outline_offset = pg.Vector2(self.outline_w, self.outline_w)
        open_surf = pg.Surface((pg.Vector2(self.num_cols, self.num_rows) * self.box_len) + outline_offset, pg.SRCALPHA)
        open_surf.fill(self.mini_map.outline_color2)
        open_surf.set_alpha(215)

        for x in range(self.num_cols + 1):
            for y in range(self.num_rows + 1):
                vert_line_x, horiz_line_y = x * self.box_len, y * self.box_len
                pg.draw.line(open_surf, self.line_color, (vert_line_x, 0), (vert_line_x, open_surf.height), self.outline_w)
                pg.draw.line(open_surf, self.line_color, (0, horiz_line_y), (open_surf.width, horiz_line_y), self.outline_w)
       
        return open_surf, open_surf.subsurface((0,0), (open_surf.width, self.box_len + outline_offset.y))

    def render(self, screen):
        topleft = self.topleft + pg.Vector2(self.outline_w, self.outline_w)
        if self.open:
            surf = self.surf_open
            rect = self.rect_open
        else:
            surf = self.surf_closed
            rect = self.rect_closed
        screen.blit(surf, rect)
        
        half_box_len = pg.Vector2(self.box_len, self.box_len) / 2
        for x in range(self.num_cols):
            for y in range(self.num_rows if self.open else 1):
                if (inv_idx := (self.num_cols * y) + x) < self.num_slots_filled:
                    if (item_name := self.item_names[inv_idx]) not in self.item_surfs:
                        self.item_surfs[item_name] = pg.transform.scale(
                            self.assets.get_img(item_name), (self.box_len * 0.75, self.box_len * 0.75)
                        )
                    item_rect = self.item_surfs[item_name].get_rect(center=topleft + (pg.Vector2(x, y) * self.box_len) + half_box_len)
                    screen.blit(self.item_surfs[item_name], item_rect)

    def check_mouse_highlight(self):
        pass

    def check_keyboard_input(self):
        if self.keyboard.pressed_keys[KEY_BINDINGS['player inv view']]:
            self.show = not self.show
            self.ui.rect.height = self.ui.update_rect_height()
        
        if self.keyboard.pressed_keys[KEY_BINDINGS['open/close player inv']]:
            self.open = not self.open
            self.rect = self.rect_open if self.open else self.rect_closed
            self.ui.rect.height = self.ui.update_rect_height()

    def update(self, screen):
        self.check_keyboard_input()
        if self.show:
            self.render(screen)