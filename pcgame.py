import pygame
import heapq
import random

pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Arial", 24)

TILE_SIZE = 40
ROWS, COLS = 9, 15
WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man with Dijkstra Ghosts")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WALL = (50, 50, 50)
PACMAN_COLOR = (255, 255, 0)
GHOST_COLOR = (255, 0, 0)
DOT_COLOR = (255, 223, 0)

# Maze layout
maze = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,0,1,0,1,0,1,0,1,1,0,1],
    [1,0,0,1,0,0,0,1,0,0,0,1,0,0,1],
    [1,1,0,1,1,1,0,1,0,1,1,1,0,1,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,0,1,0,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

pacman_pos = [1, 1]
ghost_positions = [] 
ghost_start_template = [[7, 13], [1, 13], [7, 1]]
score = 0

clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
last_move_time = 0
move_delay = 120
last_ghost_time = 0
ghost_delay = 600

AI_ALGO = None

class DisjointSet:
    def __init__(self):
        self.parent = {}
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    def union(self, x, y):
        xr, yr = self.find(x), self.find(y)
        if xr != yr:
            self.parent[yr] = xr

def kruskal_mst():
    edges = []
    for r in range(ROWS):
        for c in range(COLS):
            if maze[r][c] in [0,2]:
                for dr, dc in [(1,0),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] in [0,2]:
                        edges.append(((r,c),(nr,nc)))
    ds = DisjointSet()
    for r in range(ROWS):
        for c in range(COLS):
            if maze[r][c] in [0,2]:
                ds.parent[(r,c)] = (r,c)
    mst = {k:[] for k in ds.parent}
    for u,v in sorted(edges):
        if ds.find(u) != ds.find(v):
            ds.union(u,v)
            mst[u].append(v)
            mst[v].append(u)
    return mst

def kruskal_path(start, goal, mst):
    from collections import deque
    queue = deque([(start, [start])])
    visited = set([start])
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path[1:]  # skip start
        for neighbor in mst.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if maze[r][c] == 1:
                pygame.draw.rect(SCREEN, WALL, rect)
            else:
                pygame.draw.rect(SCREEN, WHITE, rect)
                if maze[r][c] == 0:
                    pygame.draw.circle(SCREEN, DOT_COLOR, rect.center, 6)

def draw_entities():
    pygame.draw.circle(SCREEN, PACMAN_COLOR,
                       (pacman_pos[1]*TILE_SIZE + TILE_SIZE//2, pacman_pos[0]*TILE_SIZE + TILE_SIZE//2), 15)
    for g in ghost_positions:
        pygame.draw.circle(SCREEN, GHOST_COLOR,
                           (g[1]*TILE_SIZE + TILE_SIZE//2, g[0]*TILE_SIZE + TILE_SIZE//2), 15)

def draw_score():
    text = font.render(f"Score: {score}", True, WHITE)
    SCREEN.blit(text, (10, 10))

def get_neighbors(pos):
    r, c = pos
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] in [0, 2]:
            yield (nr, nc)

def dijkstra(start, goal):
    heap = [(0, start)]
    visited = {start: None}
    while heap:
        cost, current = heapq.heappop(heap)
        if current == goal:
            break
        for neighbor in get_neighbors(current):
            if neighbor not in visited:
                visited[neighbor] = current
                heapq.heappush(heap, (cost + 1, neighbor))
    path = []
    cur = goal
    while cur and cur != start:
        path.append(cur)
        cur = visited[cur]
    path.reverse()
    return path

def move_ghosts():
    if AI_ALGO == 'dijkstra':
        for i in range(len(ghost_positions)):
            path = dijkstra(tuple(ghost_positions[i]), tuple(pacman_pos))
            if path:
                ghost_positions[i][0], ghost_positions[i][1] = path[0]
    elif AI_ALGO == 'kruskal':
        mst = kruskal_mst()
        for i in range(len(ghost_positions)):
            path = kruskal_path(tuple(ghost_positions[i]), tuple(pacman_pos), mst)
            if path:
                ghost_positions[i][0], ghost_positions[i][1] = path[0]

def check_collision():
    return any(pacman_pos == ghost for ghost in ghost_positions)

def handle_pacman_move():
    keys = pygame.key.get_pressed()
    r, c = pacman_pos
    if keys[pygame.K_DOWN] and maze[r + 1][c] in [0, 2]:
        pacman_pos[0] += 1
    elif keys[pygame.K_LEFT] and maze[r][c - 1] in [0, 2]:
        pacman_pos[1] -= 1
    elif keys[pygame.K_RIGHT] and maze[r][c + 1] in [0, 2]:
        pacman_pos[1] += 1
    elif keys[pygame.K_UP] and maze[r - 1][c] in [0, 2]:
        pacman_pos[0] -= 1

def check_victory():
    return not any(0 in row for row in maze)

def difficulty_menu():
    SCREEN.fill(BLACK)
    title = font.render("Choose Difficulty", True, WHITE)
    easy_btn = font.render("Easy (1 ghost)", True, (0, 255, 0))
    med_btn = font.render("Medium (2 ghosts)", True, (255, 165, 0))
    hard_btn = font.render("Hard (3 ghosts)", True, (255, 0, 0))

    SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    SCREEN.blit(easy_btn, (WIDTH // 2 - easy_btn.get_width() // 2, 200))
    SCREEN.blit(med_btn, (WIDTH // 2 - med_btn.get_width() // 2, 260))
    SCREEN.blit(hard_btn, (WIDTH // 2 - hard_btn.get_width() // 2, 320))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                _, y = pygame.mouse.get_pos()
                if 200 <= y <= 230:
                    return 1
                elif 260 <= y <= 290:
                    return 2
                elif 320 <= y <= 350:
                    return 3

def ai_menu():
    SCREEN.fill(BLACK)
    title = font.render("Choose Ghost AI", True, WHITE)
    dij_btn = font.render("Dijkstra (Shortest Path)", True, (0, 200, 255))
    kru_btn = font.render("Kruskal (MST Path)", True, (200, 0, 255))
    SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    SCREEN.blit(dij_btn, (WIDTH // 2 - dij_btn.get_width() // 2, 200))
    SCREEN.blit(kru_btn, (WIDTH // 2 - kru_btn.get_width() // 2, 260))
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                _, y = pygame.mouse.get_pos()
                if 200 <= y <= 230:
                    return 'dijkstra'
                elif 260 <= y <= 290:
                    return 'kruskal'

def main():
    global last_move_time, last_ghost_time, score
    running = True

    while running:
        now = pygame.time.get_ticks()

        handle_events()               # → process quitting & input
        update_pacman(now)            # → move Pac‑Man & eat dots
        update_ghosts(now)            # → move ghosts on a timer
        render_frame()                # → draw grid, entities, score
        check_end_conditions()        # → game‑over / victory screens

        clock.tick(30)                # cap FPS


def handle_events():
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


def update_pacman(now):
    global last_move_time, score
    # only move when our delay has passed
    if now - last_move_time > move_delay:
        handle_pacman_move()
        last_move_time = now

    # eat dot if we’re on one
    r, c = pacman_pos
    if maze[r][c] == 0:
        maze[r][c] = 2
        score += 1


def update_ghosts(now):
    global last_ghost_time
    if now - last_ghost_time > ghost_delay:
        move_ghosts()
        last_ghost_time = now


def render_frame():
    SCREEN.fill(BLACK)
    draw_grid()
    draw_entities()
    draw_score()
    pygame.display.flip()


def check_end_conditions():
    if check_collision():
        show_end_screen("Game Over!", (255, 50, 50))
    elif check_victory():
        show_end_screen("Congratulations! You win!", (255, 255, 0))


def show_end_screen(message, color):
    elapsed = (pygame.time.get_ticks() - start_time) // 1000
    SCREEN.fill(BLACK)
    text1 = font.render(message, True, color)
    text2 = font.render(f"Time: {elapsed} seconds", True, WHITE)
    SCREEN.blit(text1, ((WIDTH - text1.get_width())//2, HEIGHT//2 - 20))
    SCREEN.blit(text2, ((WIDTH - text2.get_width())//2, HEIGHT//2 + 20))
    pygame.display.flip()
    pygame.time.delay(5000)
    pygame.quit()
    exit()

# Setup game
AI_ALGO = ai_menu()
ghost_count = difficulty_menu()
ghost_positions.extend(ghost_start_template[:ghost_count])
main()
pygame.quit()

