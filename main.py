import pygame, sys
import pygame.gfxdraw
from pygame.locals import *
import math

FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW_BG = (255, 255, 200)
YELLOW_CELL1 = (230, 230, 150)
YELLOW_CELL2 = (240, 240, 180)
YELLOW_BEE1 = (255, 255, 100)
YELLOW_BEE2 = (200, 200, 0)

NURSE_BEE_COLOR = (210, 200, 255)
BUILDER_BEE_COLOR = (255, 200, 100)
CLEANER_BEE_COLOR = (120, 180, 255)
FOOD_MAKER_BEE_COLOR = (100, 200, 150)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
CELL_SIZE = 40
BEE_SIZE = 30
BEE_SPEED = 4
QB_SPEED = 4

SQRT3 = math.sqrt(3)

def hexagon(center, size):
    return [
            (center[0], center[1] + 2 * size),
            (center[0] - SQRT3 * size, center[1] + size),
            (center[0] - SQRT3 * size, center[1] - size),
            (center[0], center[1] - 2 * size),
            (center[0] + SQRT3 * size, center[1] - size),
            (center[0] + SQRT3 * size, center[1] + size),
        ]

def distance(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

def move_point(p, dx, dy):
    return (p[0] + dx, p[1] + dy)


class Task(object):
    pass

class TravelTo(Task):
    def __init__(self, dest):
        super().__init__()
        self.dest = dest
    
    def start(self, bee):
        self.bee = bee
        dist = distance(bee.center, self.dest)
        self.dx = (self.dest[0] - bee.center[0]) / dist * BEE_SPEED
        self.dy = (self.dest[1] - bee.center[1]) / dist * BEE_SPEED

    def update(self):
        self.bee.center = move_point(self.bee.center, self.dx, self.dy)
    
    def is_done(self):
        return distance(self.bee.center, self.dest) < 2


class Cell(pygame.sprite.Sprite):
    def __init__(self, row, col):
        super().__init__()
        y = SCREEN_HEIGHT / 2 + row * CELL_SIZE * 3 
        x = SCREEN_WIDTH / 2 + (col * 2 + row % 2) * CELL_SIZE * SQRT3
        self.rect = pygame.Rect(0, 0, CELL_SIZE * SQRT3 * 2, 2)
        self.rect.center = (x, y)
 
    def update(self):
        pass
 
    def draw(self, surface):
        points = hexagon(self.rect.center, CELL_SIZE)
        pygame.draw.polygon(surface, YELLOW_CELL1, points)
        inner_points = hexagon(self.rect.center, CELL_SIZE-5)
        pygame.draw.polygon(surface, YELLOW_CELL2, inner_points, width=10)
        pygame.draw.aalines(surface, BLACK, closed=True, points=points)


class Bee(pygame.sprite.Sprite):
    def __init__(self, x, y, job):
        super().__init__()
        self.center = (x, y)
        self.job = job
        self.tasks = []
        self.task = None

    def update(self):
        if self.task is None or self.task.is_done():
            if len(self.tasks) == 0:
                self.task = None
                return
            self.task = self.tasks[0]
            self.tasks = self.tasks[1:]
            self.task.start(self)
        else:
            self.task.update()

    def add_task(self, task):
        self.tasks.append(task)
    
    def add_tasks(self, tasks):
        for task in tasks:
            self.tasks.append(task)
    
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, BEE_SIZE)
        bee_color = YELLOW_BEE1
        if self.job == "nurse":            
            bee_color = NURSE_BEE_COLOR
        elif self.job == "builder":
            bee_color = BUILDER_BEE_COLOR
        elif self.job == "cleaner":
            bee_color = CLEANER_BEE_COLOR
        elif self.job == "food maker":
            bee_color = FOOD_MAKER_BEE_COLOR
        pygame.draw.circle(surface, bee_color, self.center, BEE_SIZE / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), BEE_SIZE, BLACK)

class QueenBee(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.center = (x, y)

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_UP] and self.center[1] > 0:
            self.center = move_point(self.center, 0, -QB_SPEED)
        if pressed_keys[K_DOWN] and self.center[1] < SCREEN_HEIGHT:
            self.center = move_point(self.center, 0, QB_SPEED)
        if pressed_keys[K_LEFT] and self.center[0] > 0:
            self.center = move_point(self.center, -QB_SPEED, 0)
        if pressed_keys[K_RIGHT] and self.center[0] < SCREEN_WIDTH:
            self.center = move_point(self.center, QB_SPEED, 0)
    
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, BEE_SIZE)
        pygame.draw.circle(surface, BLACK, self.center, BEE_SIZE / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), BEE_SIZE, BLACK)


def main():
    pygame.init()
    FramePerSec = pygame.time.Clock()
    pygame.display.set_caption("Bee Game")

    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    cells = [Cell(0, 0), Cell(1, -1), Cell(1, 0)]
    qb = QueenBee(100, 200)
    bees = [Bee(100, 100, "nurse"), Bee(200, 100, "builder"), Bee(300, 100, "cleaner"), Bee(400, 100, "food maker")]
    bees[0].add_task(TravelTo(cells[0].rect.center))
    bees[0].add_task(TravelTo(cells[1].rect.center))

    while True:
        # Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
    
        # Update
        for b in bees:
            b.update()
        qb.update()

        # Draw
        surface.fill(YELLOW_BG)
        for c in cells:
            c.draw(surface)
        for b in bees:
            b.draw(surface)
        qb.draw(surface)
        
        pygame.display.update()
        FramePerSec.tick(FPS)

if __name__ == "__main__":
    main()
