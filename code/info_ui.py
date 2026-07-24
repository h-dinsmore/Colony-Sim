import pygame as pg

from settings import KEY_BINDINGS

class InfoUI:
    def __init__(self, ui, mini_map, player, keyboard, weather, font, clock, village):
        self.ui = ui
        self.mini_map = mini_map
        self.player = player
        self.keyboard = keyboard
        self.weather = weather
        self.font = font
        self.clock = clock
        self.village = village
        
        self.surf = pg.Surface((mini_map.img.width + (self.mini_map.outline_w * self.mini_map.num_outlines * 2), 32))
        self.alpha = 215
        self.surf.set_alpha(self.alpha)

        self.default_topleft = mini_map.outline_rect2.bottomleft
        self.topleft = self.default_topleft
        self.rect = self.surf.get_rect(topleft=self.topleft)

        self.show = True

    def render(self, screen):
        self.surf.fill(self.mini_map.outline_color2)
        self.rect.topleft = self.default_topleft if self.mini_map.show else (0, 0)

        fps_surf = self.font.render(f'FPS:{self.clock.get_fps():.2f}', self.ui.anti_alias, self.ui.font_color)
        fps_rect = fps_surf.get_rect(topleft=(1,1))
        self.surf.blit(fps_surf, fps_rect)

        xyz_surf = self.font.render(f'x:{self.player.x} y:{self.player.y} z:{self.player.z}', self.ui.anti_alias, self.ui.font_color)
        xyz_rect = xyz_surf.get_rect(topleft=fps_rect.topright + pg.Vector2(30, 0))
        self.surf.blit(xyz_surf, xyz_rect)

        biome_surf = self.font.render(f'biome:{self.player.biome_in}', self.ui.anti_alias, self.ui.font_color)
        biome_rect = biome_surf.get_rect(topleft=fps_rect.bottomleft + pg.Vector2(0, 10))
        self.surf.blit(biome_surf, biome_rect)

        pop_surf = self.font.render(f'pop:{self.village.num_pop}', self.ui.anti_alias, self.ui.font_color)
        pop_rect = pop_surf.get_rect(topleft=biome_rect.topright + pg.Vector2(10, 0))
        self.surf.blit(pop_surf, pop_rect)

        date_surf = self.font.render(f'{self.weather.month} {self.weather.day}', self.ui.anti_alias, self.ui.font_color)
        date_rect = date_surf.get_rect(topleft=pop_rect.topright + pg.Vector2(10, 0))
        self.surf.blit(date_surf, date_rect)

        screen.blit(self.surf, self.rect)

    def update(self, screen):
        if self.keyboard.pressed_keys[KEY_BINDINGS['info ui view']]:
            self.show = not self.show
            self.ui.rect.height = self.ui.update_rect_height()

        if self.show:
            self.render(screen)