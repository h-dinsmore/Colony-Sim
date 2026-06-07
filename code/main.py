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
        self.world_surf = pg.Surface(RES)
        
        self.clock = pg.time.Clock()
        self.running = True

        self.assets = Assets()
        self.font = self.assets.fonts['default']

        self.cam = Camera(center_xy=(pg.Vector2(MAP_SIZE[:2]) // 2) * TILE_SIZE)

        self.keyboard = Keyboard()
        self.mouse = Mouse(self.cam.offset)

        self.proc_gen = ProcGen(self.keyboard)

        self.chunk_renderer = ChunkRenderer(self.world_surf, self.proc_gen, self.assets, self.cam.offset)

    def update(self):
        self.clock.tick(FPS) 
        self.screen.fill((0, 0, 0))
        
        self.keyboard.update()
        self.mouse.update()
        self.proc_gen.update()
        self.chunk_renderer.render()
        self.cam.update(pg.Vector2(self.proc_gen.x, self.proc_gen.y) * TILE_SIZE)

        zoom_surf = pg.transform.scale(
            self.world_surf, 
            (round(RES[0] / self.cam.zoom_ratio), round(RES[1] / self.cam.zoom_ratio))
        )
        self.screen.blit(zoom_surf, zoom_surf.get_rect(topleft=(0, 0)))
        self.screen.blit(self.font.render(f'FPS: {self.clock.get_fps():.2f}', True, 'white'), (0, 0))
        pg.display.flip()

    def run(self):
        while self.running:
            for event in pg.event.get():
                self.running = not (event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE))
                if event.type == pg.MOUSEWHEEL:
                    self.cam.zoom_ratio = max(
                        self.cam.min_zoom_ratio, 
                        min(self.cam.zoom_ratio + (event.y * 0.05), self.cam.max_zoom_ratio)
                    )
            self.update()
        pg.quit()
        sys.exit()

if __name__ == '__main__':
    Game().run()