import pygame
import heapq
import random

# Initialize
pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Arial", 24)

# Display settings
TILE_SIZE = 40
ROWS, COLS = 9, 15
WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man with Dijkstra Ghosts")

# Colors
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

# Entities
pacman_pos = [1, 1]
ghost_positions = []  # Filled at runtime based on difficulty
ghost_start_template = [[7, 13], [1, 13], [7, 1]]
score = 0

# Timers
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
last_move_time = 0
move_delay = 120
last_ghost_time = 0
ghost_delay = 600

# Draw game elements
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

# Ghost pathfinding
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
    for i in range(len(ghost_positions)):
        path = dijkstra(tuple(ghost_positions[i]), tuple(pacman_pos))
        if path:
            ghost_positions[i][0], ghost_positions[i][1] = path[0]

def check_collision():
    return any(pacman_pos == ghost for ghost in ghost_positions)

# Controls
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

# Difficulty menu
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

# Main game loop
def main():
    global last_move_time, last_ghost_time, score
    running = True
    while running:
        now = pygame.time.get_ticks()
        SCREEN.fill(BLACK)
        draw_grid()
        draw_entities()
        draw_score()
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if now - last_move_time > move_delay:
            handle_pacman_move()
            last_move_time = now

        r, c = pacman_pos
        if maze[r][c] == 0:
            maze[r][c] = 2
            score += 1

        if now - last_ghost_time > ghost_delay:
            move_ghosts()
            last_ghost_time = now

        if check_collision():
            elapsed = (pygame.time.get_ticks() - start_time) // 1000
            SCREEN.fill(BLACK)
            lose_text = font.render("Game Over!", True, (255, 50, 50))
            time_text = font.render(f" Time: {elapsed} seconds", True, WHITE)
            SCREEN.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2 - 20))
            SCREEN.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, HEIGHT // 2 + 20))
            pygame.display.flip()
            pygame.time.delay(5000)
            pygame.quit()
            exit()


        if check_victory():
            elapsed = (pygame.time.get_ticks() - start_time) // 1000
            SCREEN.fill(BLACK)
            win_text = font.render("Congratulations! You win!", True, (255, 255, 0))
            time_text = font.render(f" Time: {elapsed} seconds", True, WHITE)
            SCREEN.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 20))
            SCREEN.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, HEIGHT // 2 + 20))
            pygame.display.flip()
            pygame.time.delay(5000)
            pygame.quit()
            exit()

# Setup game
ghost_count = difficulty_menu()
ghost_positions.extend(ghost_start_template[:ghost_count])
main()
pygame.quit()

