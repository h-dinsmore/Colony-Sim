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
from mini_map import MiniMap

class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption('colony sim')
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(RES)
        self.running = True
        
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
        
        self.proc_gen = ProcGen()
        
        self.village = Village(self.proc_gen, self.assets, self.keyboard, self.world_surf)
        self.player = self.village.player
        
        self.chunk_renderer = ChunkRenderer(
            self.world_surf, self.proc_gen, self.assets, self.cam, self.player, self.keyboard
        )
        
        self.weather = Weather(self.world_surf, self.cam, self.proc_gen, self.village.village_sprs)

        self.mini_map = MiniMap(
            self.cam, self.world_surf, self.proc_gen, self.player, self.keyboard, self.chunk_renderer, 
            self.weather.sky.sky_rgb
        )

        self.info_ui_surf = pg.Surface((self.mini_map.img.width, 32))
        self.info_ui_surf.set_alpha(200)
        self.info_ui_rect = self.info_ui_surf.get_rect(
            topleft=self.mini_map.outline_rect2.bottomleft + pg.Vector2(self.mini_map.padding, 0)
        )
        self.info_ui_outline_w = 2
        self.info_ui_outline1 = pg.Rect(
            self.info_ui_rect.topleft - pg.Vector2(self.info_ui_outline_w, self.info_ui_outline_w), 
            self.info_ui_rect.size + (pg.Vector2(self.info_ui_outline_w, self.info_ui_outline_w) * 2)
        )
        self.info_ui_outline2 = pg.Rect(
            self.info_ui_outline1.topleft - pg.Vector2(self.info_ui_outline_w, self.info_ui_outline_w), 
            self.info_ui_outline1.size + (pg.Vector2(self.info_ui_outline_w, self.info_ui_outline_w) * 2)
        )

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

    def render_info_ui(self):
        self.info_ui_surf.fill(self.mini_map.outline_color2)
        anti_alias = False
        font_color = 'white'

        fps_surf = self.default_font.render(f'FPS:{self.clock.get_fps():.2f}', anti_alias, font_color)
        fps_rect = fps_surf.get_rect(topleft=(1, 1))
        self.info_ui_surf.blit(fps_surf, fps_rect)

        xyz_surf = self.default_font.render(f'x:{self.player.x} y:{self.player.y} z:{self.player.z}', anti_alias, font_color)
        xyz_rect = xyz_surf.get_rect(topleft=fps_rect.topright + pg.Vector2(5, 0))
        self.info_ui_surf.blit(xyz_surf, xyz_rect)

        biome_surf = self.default_font.render(f'biome:{self.player.biome_in}', anti_alias, font_color)
        biome_rect = biome_surf.get_rect(topleft=fps_rect.bottomleft + pg.Vector2(0, 10))
        self.info_ui_surf.blit(biome_surf, biome_rect)

        pop_surf = self.default_font.render(f'pop:{self.village.num_pop}', anti_alias, font_color)
        pop_rect = pop_surf.get_rect(topleft=biome_rect.topright + pg.Vector2(5, 0))
        self.info_ui_surf.blit(pop_surf, pop_rect)

        self.screen.blit(self.info_ui_surf, self.info_ui_rect)
       

    def update(self):
        self.clock.tick(FPS) 
        
        self.weather.update()
        self.keyboard.update()
        self.mouse.update()
        self.cam.update(pg.Vector2(self.player.rect.center))
        self.chunk_renderer.update()
        self.village.update()

        self.visible_surf = self.update_visible_surf()
        self.mini_map.update(self.visible_surf) # not blitting it on the world surface to keep it the same size when the camera zooms
        self.screen.blit(self.visible_surf, self.visible_surf.get_rect(topleft=(0, 0)))
        self.render_info_ui()
        pg.display.flip()

    def run(self):
        while self.running:
            for event in pg.event.get():
                self.running = self.player.living and not (event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE))
                if event.type == pg.MOUSEWHEEL:
                    self.cam.zoom_scale = max(
                        self.cam.min_zoom_scale, 
                        min(self.cam.zoom_scale + (event.y * 0.01), self.cam.max_zoom_scale)
                    ) 
                    
            self.update()

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()