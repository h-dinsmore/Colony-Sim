import pygame as pg
import numpy as np

from settings import RES
from alarm import Alarm

class Weather:
    def __init__(self, screen):
        self.sky = Sky(screen)

    def update(self):
        self.sky.update()

class Sky:
    def __init__(self, screen):
        self.screen = screen

        self.rgb = np.array(pg.Color('lightskyblue')[:3], dtype=int) 
        self.max_rgb = self.rgb.copy()
        self.min_rgb = np.array([0, 0, 16], dtype=int)
        self.rgb_update_dir = -1
        
        self.tint = False
        self.tint_img = pg.Surface(screen.size)
        self.tint_color = 'lightpink'
        self.tint_max_rgb = (50, 50, 100)
        self.tint_alpha = 0
        self.tint_update_dir = 1

        self.alarms = {
            'update rgb': Alarm(len=20, fn=self.update_rgb, auto=True, loop=True), 
            'update tint': Alarm(len=20, fn=self.update_tint_img, auto=False, loop=True)
        }

    def update_rgb(self):
        np.clip(np.add(self.rgb, self.rgb_update_dir, out=self.rgb), self.min_rgb, self.max_rgb, out=self.rgb)
        if np.array_equal(self.rgb, self.max_rgb) or np.array_equal(self.rgb, self.min_rgb):
            self.rgb_update_dir *= -1
    
    def check_tint(self):
        self.tint = all(0 <= self.rgb[i] <= self.tint_max_rgb[i] for i in range(3))
        if self.tint:
            if not self.alarms['update tint'].running:
                self.alarms['update tint'].start()
                self.tint_alpha = 50
                self.tint_img.fill('lightpink')
        else:
            if self.alarms['update tint'].running:
                self.alarms['update tint'].end()

    def update_tint_img(self):
        if (self.tint_alpha == 0 and self.tint_update_dir == -1) or (self.tint_alpha == 255 and self.tint_update_dir == 1):
            self.tint_update_dir *= -1
    
        self.tint_alpha += self.tint_update_dir
        self.tint_img.set_alpha(self.tint_alpha)

    def update_screen(self):
        self.screen.fill(self.rgb)
        if self.tint:
            self.screen.blit(self.tint_img, (0, 0), special_flags=pg.BLEND_RGBA_ADD)
        
    def update(self):
        self.check_tint()

        for alarm in self.alarms.values():
            alarm.update()

        self.update_screen()