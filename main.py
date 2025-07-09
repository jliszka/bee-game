import pygame, sys
import pygame.gfxdraw
from pygame.locals import *
import math

FPS = 60

BLACK = (0, 0, 0)
GRAY = (127, 127, 127)
WHITE = (255, 255, 255)
YELLOW_BG = (255, 255, 200)
YELLOW_CELL1 = (230, 230, 150)
YELLOW_CELL2 = (240, 240, 180)
YELLOW_CELL3 = (240, 240, 100)
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

pygame.init()
font = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
font_tiny = pygame.font.SysFont("Verdana", 14)
build_text = font_small.render("Build", True, GRAY)
nurse_text = font_small.render("Nurse", True, GRAY)
requested_text = font_small.render("Requested", True, GRAY)


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
    def start(self, bee):
        pass
    def update(self):
        pass
    def is_done(self):
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

class Build(Task):
    def __init__(self, cell):
        super().__init__()
        self.cell = cell
    def start(self, bee):
        self.cell.state = "building"
        self.time_remaining = FPS * 2
    def update(self):
        self.time_remaining -= 1
        if self.time_remaining == 0:
            self.cell.state = "ready"
    def is_done(self):
        return self.time_remaining == 0


def center_text(surface, rect):
    w = surface.get_width()
    h = surface.get_height()
    return move_point(rect.center, -w/2, -h/2)

def center_text1(surface, rect):
    w = surface.get_width()
    h = surface.get_height()
    return move_point(rect.center, -w/2, -h)

def center_text2(surface, rect):
    w = surface.get_width()
    return move_point(rect.center, -w/2, 0)

def button(text, color):
    text = font_tiny.render(text, True, GRAY)
    w = text.get_width() + 16
    h = text.get_height() + 10
    s = pygame.Surface((w, h))
    pygame.draw.rect(s, color, s.get_rect())
    s.blit(text, center_text(text, s.get_rect()))
    return s

class Button(object):
    def __init__(self, parent, text, color, x, y, fn):
        self.parent = parent
        self.fn = fn
        self.pos = move_point(parent.rect.topleft, x, y)
        self.rendered_text = font_tiny.render(text, True, GRAY)
        w = self.rendered_text.get_width() + 16
        h = self.rendered_text.get_height() + 10
        self.button_surface = pygame.Surface((w, h))
        pygame.draw.rect(self.button_surface, color, self.button_surface.get_rect())
        self.button_surface.blit(self.rendered_text, center_text(self.rendered_text, self.button_surface.get_rect()))

    def draw(self, surface):
        surface.blit(self.button_surface, self.pos)

    def get_rect(self):
        rect = self.button_surface.get_rect()
        rect.topleft = self.pos
        return rect

    def handle_click(self):
        self.fn()


class Cell(pygame.sprite.Sprite):
    def __init__(self, row, col):
        super().__init__()
        y = SCREEN_HEIGHT / 2 + row * CELL_SIZE * 3 
        x = SCREEN_WIDTH / 2 + (col * 2 + row % 2) * CELL_SIZE * SQRT3
        self.rect = pygame.Rect(0, 0, CELL_SIZE * SQRT3 * 2, CELL_SIZE * 2)
        self.rect.center = (x, y)
        self.state = "unbuilt"
        self.buttons = [
            Button(self, "Nursery", NURSE_BEE_COLOR, 20, 0, self.make_nursery),
            Button(self, "Bee bread", FOOD_MAKER_BEE_COLOR, 20, 30, self.request_food_maker),
            Button(self, "Honey", BUILDER_BEE_COLOR, 20, 60, self.request_food_maker),
        ]
 
    def update(self):
        pass

    def make_nursery(self):
        self.state = "nursery"
 
    def request_food_maker(self):
        food_makers = [ bee for bee in bees if bee.job == "food maker" ]
        if len(food_makers) > 0:
            self.state = "food maker requested"
            orig_pos = food_makers[0].center
            food_makers[0].add_tasks([
                TravelTo(self.rect.center),
                TravelTo(orig_pos)
            ])

    def draw(self, surface):
        if self.state == "unbuilt" or self.state == "build requested":
            border_color = YELLOW_CELL1
            bg_color = YELLOW_CELL2
        elif self.state == "building":
            border_color = YELLOW_CELL2
            bg_color = YELLOW_CELL1
        elif self.state == "nursery":
            border_color = NURSE_BEE_COLOR
            bg_color = YELLOW_CELL3
        else:
            border_color = BUILDER_BEE_COLOR
            bg_color = YELLOW_CELL3
        points = hexagon(self.rect.center, CELL_SIZE)
        pygame.draw.polygon(surface, bg_color, points)
        inner_points = hexagon(self.rect.center, CELL_SIZE-2)
        pygame.draw.polygon(surface, border_color, inner_points, width=7)
        pygame.draw.aalines(surface, BLACK, closed=True, points=points)
        if self.state == "unbuilt" and self.rect.collidepoint(pygame.mouse.get_pos()):
            surface.blit(build_text, center_text(build_text, self.rect))
        elif self.state == "build requested":
            surface.blit(build_text, center_text1(build_text, self.rect))
            surface.blit(requested_text, center_text2(requested_text, self.rect))
        elif self.state == "nurse requested":
            surface.blit(nurse_text, center_text1(nurse_text, self.rect))
            surface.blit(requested_text, center_text2(requested_text, self.rect))
        elif self.state == "ready" and self.rect.collidepoint(pygame.mouse.get_pos()):
            for button in self.buttons:
                button.draw(surface)


    def handle_click(self):
        if self.state == "unbuilt":
            builders = [ bee for bee in bees if bee.job == "builder" ]
            if len(builders) > 0:
                self.state = "build requested"
                orig_pos = builders[0].center
                builders[0].add_tasks([
                    TravelTo(self.rect.center),
                    Build(self),
                    TravelTo(orig_pos)
                ])
        elif self.state == "ready":
            for button in self.buttons:
                if button.get_rect().collidepoint(pygame.mouse.get_pos()):
                    button.handle_click()

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
        size = BEE_SIZE
        bee_color = YELLOW_BEE1
        if self.job == "nurse":            
            bee_color = NURSE_BEE_COLOR
        elif self.job == "builder":
            bee_color = BUILDER_BEE_COLOR
            size *= 1.2
        elif self.job == "cleaner":
            bee_color = CLEANER_BEE_COLOR
        elif self.job == "food maker":
            bee_color = FOOD_MAKER_BEE_COLOR
            size *= 1.2
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, size)
        pygame.draw.circle(surface, bee_color, self.center, size / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), int(size), BLACK)

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
        size = BEE_SIZE * 1.5
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, size)
        pygame.draw.circle(surface, BLACK, self.center, size / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), int(size), BLACK)


cells = [Cell(0, 0), Cell(1, -1), Cell(1, 0)]
qb = QueenBee(100, 200)
bees = [Bee(100, 100, "nurse"), Bee(200, 100, "builder"), Bee(300, 100, "cleaner"), Bee(400, 100, "food maker")]

def main():
    FramePerSec = pygame.time.Clock()
    pygame.display.set_caption("Bee Game")

    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while True:
        # Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                for cell in cells:
                    if cell.rect.collidepoint(pygame.mouse.get_pos()):
                        cell.handle_click()
                        break
    
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
