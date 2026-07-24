import pygame as pg

from settings import KEY_BINDINGS, TILE_SIZE
from os.path import join

class PlayerInventoryUI:
    def __init__(self, ui, player, mini_map, assets, keyboard, mouse):
        self.ui = ui
        self.player = player
        self.mini_map = mini_map
        self.assets = assets
        self.keyboard = keyboard
        self.mouse = mouse
        
        self.line_w = 1
        self.line_color = self.mini_map.outline_color2
        self.num_cols = 8
        self.num_rows = player.max_slot_storage // self.num_cols
        self.slot_len = self.mini_map.outline_rect2.width // self.num_cols
    
        self.num_slots_filled = len(player.inv)
        self.item_names = list(player.inv)
        self.item_surfs = {}
        self.show = True
        self.open = False # show only the first row or the full inventory
        
        self.surf_color = 'black'
        self.alpha = 228
        self.surf_open, self.surf_closed = self.get_surfs()

        self.rect_open = self.surf_open.get_rect(topleft=self.mini_map.outline_rect2.bottomleft)
        self.rect_closed = self.surf_closed.get_rect(topleft=self.rect_open.topleft)
        self.rect = self.rect_closed
        self.old_topleft = None
        self.topleft = self.update_topleft()

        self.slot_overlap_idx = None
        self.slot_highlight_surf = pg.Surface((self.slot_len, self.slot_len))
        self.slot_highlight_surf.fill(pg.Color(self.surf_color)[:3] + pg.Vector3(32))
        self.slot_highlight_surf.set_alpha(self.alpha)

    def update_topleft(self):
        if (topleft := self.mini_map.outline_rect2.bottomleft if self.mini_map.show else pg.Vector2()) != self.old_topleft:
            self.old_topleft = topleft
            self.rect_open.topleft = topleft
            self.rect_closed.topleft = topleft
        return topleft

    def get_surfs(self):
        open_surf = pg.Surface((pg.Vector2(self.num_cols, self.num_rows) * self.slot_len), pg.SRCALPHA)
        open_surf.fill(self.surf_color)
        open_surf.set_alpha(self.alpha)

        for x in range(1, self.num_cols):
            vert_line_x = x * self.slot_len
            pg.draw.line(open_surf, self.line_color, (vert_line_x, 0), (vert_line_x, open_surf.height), self.line_w)
        
        for y in range(1, self.num_rows):
            horiz_line_y = y * self.slot_len
            pg.draw.line(open_surf, self.line_color, (0, horiz_line_y), (open_surf.width, horiz_line_y), self.line_w)
        
        return open_surf, open_surf.subsurface((0,0), (open_surf.width, self.slot_len + self.line_w))

    def render(self, screen):
        if self.open:
            surf = self.surf_open.copy()
            rect = self.rect_open
        else:
            surf = self.surf_closed.copy()
            rect = self.rect_closed

        half_slot_len = pg.Vector2(self.slot_len, self.slot_len) / 2
        mouse_overlap = self.slot_overlap_idx is not None
        for x in range(self.num_cols):
            for y in range(self.num_rows if self.open else 1):
                slot_has_item = (inv_idx := (self.num_cols * y) + x) < (self.num_slots_filled if self.open else min(self.num_cols, self.num_slots_filled))

                if mouse_overlap and (x, y) == self.slot_overlap_idx:
                    self.render_mouse_overlap(surf, x, y, slot_has_item, inv_idx, screen)
                
                if slot_has_item:
                    if (item_name := self.item_names[inv_idx]) not in self.item_surfs:
                        self.item_surfs[item_name] = pg.transform.scale(self.assets.get_img(item_name), (self.slot_len * 0.75, self.slot_len * 0.75))
                    surf.blit(self.item_surfs[item_name], self.item_surfs[item_name].get_rect(center=(pg.Vector2(x, y) * self.slot_len) + half_slot_len))

                    if (item_amount := str(self.player.inv[item_name]['amount'])) not in self.assets.font_text_cache['inv item amounts']:
                        self.assets.font_text_cache['inv item amounts'][item_amount] = self.assets.fonts['inv item amounts'].render(
                            item_amount, self.ui.anti_alias, self.ui.font_color
                        )
                    font_surf = self.assets.font_text_cache['inv item amounts'][item_amount]
                    surf.blit(font_surf, font_surf.get_rect(bottomright=(pg.Vector2(x, y) * self.slot_len) + pg.Vector2(self.slot_len - 1)))
                    
        screen.blit(surf, rect)

    def check_mouse_overlap(self):
        mx, my = self.mouse.screen_pos
        if self.rect.collidepoint(mx, my):
            slot_x = mx // self.slot_len
            slot_y = (my - self.rect.top) // self.slot_len
            self.slot_overlap_idx = (int(slot_x), int(slot_y))
        else:
            self.slot_overlap_idx = None

    def render_mouse_overlap(self, surf, x, y, slot_has_item, inv_idx, screen):
        surf.blit(self.slot_highlight_surf, self.slot_highlight_surf.get_rect(topleft=pg.Vector2(x, y) * self.slot_len))
        if slot_has_item:
            if (item_name := self.item_names[inv_idx]) not in self.assets.font_text_cache['inv item names']:
                text_surf = self.assets.fonts['inv item names'].render(item_name, self.ui.anti_alias, self.ui.font_color)
                self.assets.font_text_cache['inv item names'][item_name] = {'text': text_surf}
                
                bg_surf = pg.Surface(text_surf.size + pg.Vector2(4), pg.SRCALPHA)
                bg_surf.set_alpha(surf.get_alpha())
                bg_surf.fill('black')
                self.assets.font_text_cache['inv item names'][item_name]['bg'] = bg_surf

            text_surf, bg_surf = self.assets.font_text_cache['inv item names'][item_name].values()
            if (slot_below_row1 := inv_idx > self.num_cols) or self.open:
                render_surf = surf 
                topleft = pg.Vector2(x, y) * self.slot_len + pg.Vector2(0, self.slot_len + self.line_w)
            else:
                render_surf = screen # avoids getting cropped out by the subsurface
                topleft = (self.rect.topleft + (pg.Vector2(x, y) * self.slot_len) + pg.Vector2(0, self.slot_len + self.line_w))

            render_surf.blit(bg_surf, bg_surf.get_rect(topleft=topleft))
            render_surf.blit(text_surf, text_surf.get_rect(topleft=topleft + pg.Vector2(2)))

    def check_keyboard_input(self):
        if self.keyboard.pressed_keys[KEY_BINDINGS['player inv view']]:
            self.show = not self.show
            self.ui.rect.height = self.ui.update_rect_height()
            self.update_topleft()
        
        if self.keyboard.pressed_keys[KEY_BINDINGS['open/close player inv']]:
            self.open = not self.open
            self.rect = self.rect_open if self.open else self.rect_closed
            self.ui.rect.height = self.ui.update_rect_height()
            self.update_topleft()

    def update(self, screen):
        self.check_keyboard_input()
        self.check_mouse_overlap()
        if self.show:
            self.render(screen)