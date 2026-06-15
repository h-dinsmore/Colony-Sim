import pygame as pg

from os import walk
from os.path import join
from pathlib import Path
from dataclasses import dataclass, field
from settings import TILE_SIZE

@dataclass
class FolderDir:
    files: dict[str, pg.Surface | None] = field(default_factory=dict)
    subfolders: dict[str, 'FolderDir'] = field(default_factory=dict)
    loaded: bool = False

class Assets:
    def __init__(self):
        self.graphics_load_runtime = {'entities', 'terrain'} 
        self.graphics_dir_root = Path('..') / 'graphics'
        self.graphics = {
            folder.name: self.load_subfolders(folder, folder.name in self.graphics_load_runtime) 
            for folder in self.graphics_dir_root.iterdir() if folder.is_dir()
        }
        self.img_cache, self.folder_cache = {}, {}

        self.colors = {
            'text': 'darkorchid',
            'sky': 'lightskyblue'
        }
        
        self.font_sizes = {'default': 16}
        self.fonts = self.load_fonts(join('..', 'graphics', 'fonts'))

    @staticmethod
    def load_img(dir_path):
        return pg.transform.scale(pg.image.load(dir_path).convert_alpha(), (TILE_SIZE, TILE_SIZE))
    
    def load_folder(self, dir_path):
        imgs = {}
        for path, _, files in walk(dir_path):    
            for name in files:
                key = name.split('.')[0] # not reassigning 'name' because it needs the file extension when passed to load_img()
                imgs[int(key) if key.isnumeric() else key] = self.load_img(join(path, name))
        return imgs
    
    def load_frames(self, dir_path):
        frames = []
        for path, _, files in walk(dir_path):   
            for file in sorted(files, key=lambda name: int(name.split('.')[0])): 
                frames.append(self.load_img(join(path, file)))
        return frames

    def load_subfolders(self, dir_path, load_files=False):
        folder_dir = FolderDir(loaded=load_files)
        if load_files:
            folder_dir.files = self.load_folder(dir_path)

        for folder in (f for f in dir_path.iterdir() if f.is_dir()):
            folder_dir.subfolders[folder.name] = self.load_subfolders(folder, load_files)
        return folder_dir

    def get_folder(self, dir_path):
        if dir_path in self.folder_cache:
            return self.folder_cache[dir_path]
        
        dir_parts = Path(dir_path).relative_to(self.graphics_dir_root).parts
        current_folder = self.graphics[dir_parts[0]] 

        for folder in dir_parts[1:]: 
            current_folder = current_folder.subfolders[folder]

        if not current_folder.loaded:
            files = self.load_folder(dir_path)
            current_folder.files = files
            current_folder.loaded = True
            self.folder_cache[dir_path] = files
        return current_folder
    
    def get_img(self, dir_path):
        if dir_path in self.img_cache:
            return self.img_cache[dir_path]
        
        img = self.load_img(dir_path)
        self.img_cache[dir_path] = img
        return img
    
    def load_fonts(self, dir_path):
        fonts = {}
        for path, _, files in walk(dir_path):    
            for name in files:
                name_split = name.split('.')[0]
                fonts[name_split] = pg.font.Font(join(path, name), self.font_sizes[name_split])
        return fonts