import pygame as pg
import sys

from settings import RES, FPS, MAP_SIZE, TILE_SIZE
from assets import Assets
from camera import Camera
from input import Keyboard, Mouse
from proc_gen import ProcGen
from chunk_renderer import ChunkRenderer

class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption('colony sim')
        self.screen = pg.display.set_mode(RES)
        self.world_surf, self.visible_surf = pg.Surface((MAP_SIZE[0] * TILE_SIZE, MAP_SIZE[1] * TILE_SIZE)), pg.Surface(RES)
        self.clock = pg.time.Clock()
        self.running = True

        self.assets = Assets()
        self.default_font = self.assets.fonts['default']
        
        self.keyboard = Keyboard()
        
        self.cam = Camera((pg.Vector2(MAP_SIZE[:2]) // 2) * TILE_SIZE, self.keyboard)
        self.cam_offset = None
        self.zoom_scale = None

        self.mouse = Mouse(self.cam.offset)

        self.proc_gen = ProcGen(self.keyboard)
        self.z = None

        self.chunk_renderer = ChunkRenderer(self.world_surf, self.proc_gen, self.assets, self.cam.offset)

    def update_visible_surf(self): 
        dif_offset = self.cam.offset != self.cam_offset
        dif_zoom = self.cam.zoom_scale != self.zoom_scale
        dif_z = self.proc_gen.z != self.z
        if dif_offset or dif_zoom or dif_z:
            if dif_offset:
                self.cam_offset = self.cam.offset.copy()
            if dif_zoom:
                self.zoom_scale = self.cam.zoom_scale
            if dif_z:
                self.z = self.proc_gen.z

            return pg.transform.scale(
                self.world_surf.subsurface(self.cam_offset, (round(RES[0] / self.zoom_scale), round(RES[1] / self.zoom_scale))), RES
            )
        
        return self.visible_surf

    def update(self):
        self.clock.tick(FPS) 
        self.screen.fill((0, 0, 0))
        
        self.keyboard.update()
        self.mouse.update()
        self.proc_gen.update()
        self.cam.update(pg.Vector2(self.proc_gen.x, self.proc_gen.y) * TILE_SIZE)
        self.chunk_renderer.render()
        
        self.visible_surf = self.update_visible_surf()
        self.screen.blit(self.visible_surf, self.visible_surf.get_rect(topleft=(0, 0)))
        self.screen.blit(
            self.default_font.render(
                f'FPS: {self.clock.get_fps():.2f} x: {self.proc_gen.x}, y: {self.proc_gen.y} z: {self.proc_gen.z}', 
                True, 'white'), (0, 0)
        )
        pg.display.flip()

    def run(self):
        while self.running:
            for event in pg.event.get():
                self.running = not (event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE))
                if event.type == pg.MOUSEWHEEL:
                    self.cam.zoom_scale = max(
                        self.cam.min_zoom_scale, 
                        min(self.cam.zoom_scale + event.y * 0.01, self.cam.max_zoom_scale)
                    )
            self.update()
        pg.quit()
        sys.exit()

if __name__ == '__main__':
    Game().run()