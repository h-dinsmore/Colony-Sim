import pygame as pg
import numpy as np

from settings import RES
from alarm import Alarm

class Weather:
    def __init__(self, world_surf, cam):
        self.sky = Sky(world_surf, cam)

    def update(self):
        self.sky.update()

class Sky:
    def __init__(self, world_surf, cam):
        self.world_surf = world_surf
        self.cam = cam

        self.rgb = np.array(pg.Color('lightskyblue')[:3], dtype=int) 
        self.max_rgb = self.rgb.copy()
        self.min_rgb = np.array([0, 0, 64], dtype=int)
        self.rgb_update_dir = -1
        
        self.tint = False
        self.tint_img = pg.Surface(RES, pg.SRCALPHA)
        self.tint_img.fill('lightpink')
        self.rgbs_activate_tint = {
            'sunrise': np.array([88, 88, 152], dtype=np.uint8), 
            'sunset': np.array([48, 119, 163], dtype=np.uint8)
        }
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
        if self.tint:
            self.tint = self.tint_update_dir > 0 or self.tint_alpha > 0
        else:
            self.tint = np.array_equal(self.rgb, self.rgbs_activate_tint['sunrise']) or np.array_equal(self.rgb, self.rgbs_activate_tint['sunset'])
        
        if self.tint:
            if not self.alarms['update tint'].running:
                self.alarms['update tint'].start()
        else:
            if self.alarms['update tint'].running:
                self.alarms['update tint'].end()
                self.tint_update_dir = 1
                self.tint_alpha = 0
                self.world_surf.fill(self.rgb)

    def update_tint_img(self):
        if self.tint_alpha == 255:
            self.tint_update_dir *= -1
        
        self.tint_alpha += self.tint_update_dir
        self.tint_img.set_alpha(self.tint_alpha)

    def update_screen(self):
        subsurf = self.world_surf.subsurface(
            self.cam.offset, 
            (RES[0] / self.cam.zoom_scale, RES[1] / self.cam.zoom_scale)
        )

        if self.tint:
            self.tint_img = pg.transform.scale(self.tint_img, subsurf.size)
            self.tint_img.set_alpha(self.tint_alpha)
            subsurf.blit(self.tint_img, (0, 0))
        else:
            subsurf.fill(self.rgb)

    def update(self):
        self.check_tint()
        if self.tint:
            self.alarms['update tint'].update()
        else:
            self.alarms['update rgb'].update()

        self.update_screen()