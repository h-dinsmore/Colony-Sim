import pygame as pg

class Alarm:
    def __init__(self, len, fn=None, auto=False, loop=False, *args, **kwargs):
        self.len = len
        self.fn = fn
        self.loop = loop
        self.args = args
        self.kwargs = kwargs

        self.running = False
        if auto: 
            self.start()

    def start(self):
        self.running = True
        self.start_time = pg.time.get_ticks()

    def end(self) -> None:
        self.running = False
        self.start_time = 0

        if self.fn:
            self.fn(*self.args, **self.kwargs)

        if self.loop:
            self.start()

    def update(self) -> None:
        if self.running:
            if pg.time.get_ticks() - self.start_time >= self.len:
                self.end()