import pygame as pg
import sys

from settings import RES, FPS, MAP_PX_SIZE, TILE_SIZE
from assets import Assets
from camera import Camera
from input import Keyboard, Mouse
from proc_gen import ProcGen
from chunk_renderer import ChunkRenderer
from weather import Weather
from village import Village

class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption('colony sim')
        self.clock = pg.time.Clock()
        self.running = True
        self.screen = pg.display.set_mode(RES)
        
        self.keyboard = Keyboard()
        
        self.cam = Camera(pg.Vector2(RES) / 2, self.keyboard)
        self.zoom_scale = None
        
        self.mouse = Mouse(self.cam.offset)

        self.world_surf = pg.Surface(
            (MAP_PX_SIZE[0] / self.cam.min_zoom_scale, 
             MAP_PX_SIZE[1] / self.cam.min_zoom_scale), 
            pg.SRCALPHA
        )
        self.visible_surf = None
        
        self.assets = Assets()
        self.default_font = self.assets.fonts['default']
        
        self.proc_gen = ProcGen(self.keyboard)
        
        self.village = Village(self.proc_gen, self.assets, self.keyboard, self.world_surf)
        self.player = self.village.player
        
        self.chunk_renderer = ChunkRenderer(self.world_surf, self.proc_gen, self.assets, self.cam, self.player)
        
        self.weather = Weather(self.world_surf, self.cam, self.proc_gen, self.village.village_sprs)

    def update_visible_surf(self): 
        scaled_res_x, scaled_res_y = round(RES[0] / self.cam.zoom_scale), round(RES[1] / self.cam.zoom_scale)
        max_x, max_y = self.world_surf.width - scaled_res_x, self.world_surf.height - scaled_res_y
        cam_x, cam_y = self.cam.offset
        return pg.transform.scale(
            self.world_surf.subsurface(
                (max(0, min(cam_x, max_x)), max(0, min(cam_y, max_y))), 
                (scaled_res_x, scaled_res_y)
            ), 
            RES
        )
        
    def update(self):
        self.clock.tick(FPS) 
        
        self.weather.update()
        self.keyboard.update()
        self.mouse.update()
        self.proc_gen.update(self.player.z)
        self.cam.update(pg.Vector2(self.player.rect.center))
        self.chunk_renderer.render()
        self.village.update()

        self.visible_surf = self.update_visible_surf()
        self.screen.blit(self.visible_surf, self.visible_surf.get_rect(topleft=(0, 0)))
        self.screen.blit(
            self.default_font.render(
                f'FPS: {self.clock.get_fps():.2f} x: {self.player.x}, y: {self.player.y} z: {self.player.z}', 
                True, 'white'), (0, 0)
        )
        pg.display.flip()

    def run(self):
        while self.running:
            self.update_screen = False
            for event in pg.event.get():
                self.running = not (event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE))
                if event.type == pg.MOUSEWHEEL:
                    self.cam.zoom_scale = max(
                        self.cam.min_zoom_scale, 
                        min(self.cam.zoom_scale + (event.y * 0.01), self.cam.max_zoom_scale)
                    ) 
                    
            self.update()

        pg.quit()
        sys.exit()

if __name__ == '__main__':
    Game().run()