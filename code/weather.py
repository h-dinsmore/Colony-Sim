import pygame as pg
import numpy as np
from random import randint

from settings import RES, MONTHS_DAYS, MONTH_IDXS, MOON_PHASES, MOON_PHASE_IDXS
from alarm import Alarm

class Weather:
    def __init__(self, world_surf, cam, proc_gen, village_sprs):
        self.sky = Sky(self, world_surf, cam)
        self.proc_gen = proc_gen
        self.village_sprs = village_sprs

        self.month_idx = randint(0, len(MONTHS_DAYS) - 1)
        self.month = MONTH_IDXS[self.month_idx]
        self.day = randint(0, MONTHS_DAYS[self.month])

        self.moon_phase_idx = randint(0, len(MOON_PHASES) - 1)
        self.moon_phase = MOON_PHASE_IDXS[self.moon_phase_idx]
        
    def update_calendar(self):
        if self.day < MONTHS_DAYS[self.month]:
            self.day += 1
        else:
            self.day = 1
            self.month_idx = (self.month_idx + 1) % len(MONTHS_DAYS)
            self.month = self.month_idxs[self.month_idx]

        self.moon_phase_idx = (self.moon_phase_idx + 1) % len(MOON_PHASES)
        self.moon_phase = self.moon_phase_idxs[self.moon_phase_idx]

        for spr in [s for s in self.village_sprs if s.birthday == f'{self.month} {self.day}']:
            spr.age += 1

    def update(self):
        self.sky.update()

class Sky:
    def __init__(self, weather, world_surf, cam):
        self.weather = weather
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
            'update rgb': Alarm(len=10_000, fn=self.update_rgb, auto=True, loop=True), 
            'update tint': Alarm(len=10_000, fn=self.update_tint_img, auto=False, loop=True)
        }

    def update_rgb(self):
        np.clip(np.add(self.rgb, self.rgb_update_dir, out=self.rgb), self.min_rgb, self.max_rgb, out=self.rgb)
        midnight = np.array_equal(self.rgb, self.min_rgb)
        if np.array_equal(self.rgb, self.max_rgb) or midnight:
            self.rgb_update_dir *= -1
        
        if midnight:
            self.weather.update_calendar()
    
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