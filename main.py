import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
is_fullscreen = False
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro 2D Shooter - by OG-Jaggman - Made using Pygame and Visual Studio Code")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
            self.rect.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def shoot(self):
        return Bullet(self.rect.centerx, self.rect.top, -10)  # Up

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-100, -40)
        self.speed = random.randint(1, 3)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Score
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

# Enemy spawn rate
enemy_spawn_rate = 60  # Spawn every second at 60 FPS

# Load high score
try:
    with open('highscore.txt', 'r') as f:
        highscore = int(f.read().strip())
except FileNotFoundError:
    highscore = 0

def run_game():
    global highscore
    while True:  # Loop for retries
        # Initialize game state
        all_sprites = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()

        player = Player()
        all_sprites.add(player)

        score = 0
        enemy_timer = 0
        paused = False

        # Pause menu rects
        resume_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 40, 120, 40)
        give_up_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 10, 120, 40)
        main_menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 60, 160, 40)

        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not paused:
                        bullet = player.shoot()
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                    elif event.key == pygame.K_ESCAPE:
                        paused = not paused
                elif event.type == pygame.MOUSEBUTTONDOWN and not paused:
                    if event.button == 1:  # left click
                        bullet = player.shoot()
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                elif event.type == pygame.MOUSEBUTTONDOWN and paused:
                    if resume_rect.collidepoint(event.pos):
                        paused = False
                    elif give_up_rect.collidepoint(event.pos):
                        running = False
                    elif main_menu_rect.collidepoint(event.pos):
                        return 'menu'

            if not paused:
                # Update
                all_sprites.update()

                # Spawn enemies
                enemy_timer += 1
                if enemy_timer >= enemy_spawn_rate:
                    enemy = Enemy()
                    all_sprites.add(enemy)
                    enemies.add(enemy)
                    enemy_timer = 0

                # Check collisions
                hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
                for hit in hits:
                    score += 10
                    if score > highscore:
                        highscore = score

                # Check if enemy hits player
                if pygame.sprite.spritecollideany(player, enemies):
                    running = False

            # Fill the screen with black
            screen.fill(BLACK)

            # Draw all sprites
            all_sprites.draw(screen)

            # Draw score
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            highscore_text = font.render(f"High Score: {highscore}", True, WHITE)
            screen.blit(highscore_text, (10, 40))

            if paused:
                # Draw pause menu
                pause_text = font.render("Paused", True, WHITE)
                resume_text = font.render("Resume", True, WHITE)
                give_up_text = font.render("Give Up", True, WHITE)
                main_menu_text = font.render("Main Menu", True, WHITE)
                screen.blit(pause_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 80))
                pygame.draw.rect(screen, WHITE, resume_rect, 2)
                screen.blit(resume_text, resume_text.get_rect(center=resume_rect.center))
                pygame.draw.rect(screen, WHITE, give_up_rect, 2)
                screen.blit(give_up_text, give_up_text.get_rect(center=give_up_rect.center))
                pygame.draw.rect(screen, WHITE, main_menu_rect, 2)
                screen.blit(main_menu_text, main_menu_text.get_rect(center=main_menu_rect.center))

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(FPS)

        # Save high score
        with open('highscore.txt', 'w') as f:
            f.write(str(highscore))

        # Game over screen
        screen.fill(BLACK)
        game_over_text = font.render("Game Over", True, WHITE)
        final_score_text = font.render(f"Final Score: {score}", True, WHITE)
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        highscore_text = font.render(f"High Score: {highscore}", True, WHITE)
        screen.blit(highscore_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))
        retry_text = font.render("Retry", True, WHITE)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        menu_text = font.render("Main Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        pygame.draw.rect(screen, WHITE, retry_rect.inflate(20, 10), 2)
        screen.blit(retry_text, retry_rect)
        pygame.draw.rect(screen, WHITE, menu_rect.inflate(20, 10), 2)
        screen.blit(menu_text, menu_rect)
        pygame.display.flip()

        # Wait for retry, menu, or quit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if retry_rect.collidepoint(event.pos):
                        waiting = False
                        # Continue the outer loop for retry
                    elif menu_rect.collidepoint(event.pos):
                        waiting = False
                        return 'menu'
# Main menu
current_screen = 'menu'

# Button rects
start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 200, 200, 50)
directions_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 270, 200, 50)
credits_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 340, 200, 50)
update_log_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 410, 200, 50)
toggle_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, 480, 250, 50)
back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 60, 100, 40)

# Load texts
with open('directions.txt', 'r') as f:
    directions_text = f.read()
with open('credits.txt', 'r') as f:
    credits_text = f.read()
with open('Update Log.txt', 'r') as f:
    update_log_text = f.read()

# Main loop
running = True
while running:
    if current_screen == 'menu':
        screen.fill(BLACK)
        title_text = font.render("Retro 2D Shooter - by OG-Jaggman", True, WHITE)
        start_text = font.render("Start Game", True, WHITE)
        directions_text_menu = font.render("Directions", True, WHITE)
        credits_text_menu = font.render("Game Credits", True, WHITE)
        update_log_text_menu = font.render("Update Log", True, WHITE)
        toggle_text = font.render("Toggle Fullscreen", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - 150, 100))
        pygame.draw.rect(screen, WHITE, start_rect, 2)
        screen.blit(start_text, start_text.get_rect(center=start_rect.center))
        pygame.draw.rect(screen, WHITE, directions_rect, 2)
        screen.blit(directions_text_menu, directions_text_menu.get_rect(center=directions_rect.center))
        pygame.draw.rect(screen, WHITE, credits_rect, 2)
        screen.blit(credits_text_menu, credits_text_menu.get_rect(center=credits_rect.center))
        pygame.draw.rect(screen, WHITE, update_log_rect, 2)
        screen.blit(update_log_text_menu, update_log_text_menu.get_rect(center=update_log_rect.center))
        pygame.draw.rect(screen, WHITE, toggle_rect, 2)
        screen.blit(toggle_text, toggle_text.get_rect(center=toggle_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    current_screen = 'game'
                elif directions_rect.collidepoint(event.pos):
                    current_screen = 'directions'
                elif credits_rect.collidepoint(event.pos):
                    current_screen = 'credits'
                elif update_log_rect.collidepoint(event.pos):
                    current_screen = 'update_log'
                elif toggle_rect.collidepoint(event.pos):
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    elif current_screen == 'directions':
        screen.fill(BLACK)
        y = 50
        for line in directions_text.split('\n'):
            line_text = small_font.render(line, True, WHITE)
            screen.blit(line_text, (50, y))
            y += 30
        back_text = font.render("Back", True, WHITE)
        pygame.draw.rect(screen, WHITE, back_rect, 2)
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    current_screen = 'menu'

    elif current_screen == 'credits':
        screen.fill(BLACK)
        y = 50
        for line in credits_text.split('\n'):
            line_text = small_font.render(line, True, WHITE)
            screen.blit(line_text, (50, y))
            y += 30
        back_text = font.render("Back", True, WHITE)
        pygame.draw.rect(screen, WHITE, back_rect, 2)
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    current_screen = 'menu'

    elif current_screen == 'update_log':
        screen.fill(BLACK)
        y = 50
        for line in update_log_text.split('\n'):
            line_text = small_font.render(line, True, WHITE)
            screen.blit(line_text, (50, y))
            y += 30
        back_text = font.render("Back", True, WHITE)
        pygame.draw.rect(screen, WHITE, back_rect, 2)
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    current_screen = 'menu'

    elif current_screen == 'game':
        result = run_game()
        if result == 'quit':
            running = False
        else:
            current_screen = result

# Quit Pygame
pygame.quit()
sys.exit()

# Quit Pygame
pygame.quit()
sys.exit()