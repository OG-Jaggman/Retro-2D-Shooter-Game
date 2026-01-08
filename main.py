import os
import sys

# Enforce Windows-only support early
if os.name != "nt":
    _msg = "Sorry, this game currently only supports Windows."
    try:
        import tkinter as _tk
        from tkinter import messagebox as _messagebox
        _root = _tk.Tk()
        _root.withdraw()
        _messagebox.showerror("Unsupported OS", _msg)
        _root.destroy()
    except Exception:
        pass
    sys.stderr.write(_msg + "\n")
    raise SystemExit(1)

import pygame
import random
import tkinter as tk
from tkinter import simpledialog

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

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
YELLOW = (255, 255, 0)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Prompt for user email

# Custom login window with Advanced button
def get_user_email():
    result = {'email': None}
    def show_advanced():
        main_frame.pack_forget()
        advanced_frame.pack(fill='both', expand=True)
    def back_to_main():
        advanced_frame.pack_forget()
        main_frame.pack(fill='both', expand=True)
    def sign_in_guest():
        result['email'] = 'guest@example.com'
        root.quit()
    def login():
        email = email_entry.get().strip()
        result['email'] = email if email else None
        root.quit()
    def close_game():
        root.destroy()
        sys.exit()
    root = tk.Tk()
    root.title('Login')
    root.geometry('400x220')
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    tk.Label(main_frame, text="Enter your email for high score tracking:").pack(pady=(20,5))
    email_entry = tk.Entry(main_frame, width=30)
    email_entry.pack(pady=5)
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="Login", width=12, command=login).pack(side='left', padx=10)
    tk.Button(btn_frame, text="Advanced", width=12, command=show_advanced).pack(side='left', padx=10)
    tk.Button(btn_frame, text="Close Game", width=12, command=close_game).pack(side='left', padx=10)
    advanced_frame = tk.Frame(root)
    tk.Label(advanced_frame, text="About logging in:", font=(None, 12, 'bold')).pack(pady=(20,0))
    tk.Label(advanced_frame, text="Logging in with your email lets you save your high score to the cloud and access it from any device.", wraplength=350).pack(padx=10, pady=5)
    tk.Button(advanced_frame, text="Sign in as a guest (won't keep your high score)", command=sign_in_guest).pack(pady=10)
    tk.Button(advanced_frame, text="Back", command=back_to_main).pack(pady=(0,10))
    root.mainloop()
    root.destroy()
    return result['email'] if result['email'] else 'guest@example.com'

# Firestore high score functions

def load_highscore(email):
    try:
        doc_ref = db.collection('highscores').document(email)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('score', 0)
    except Exception as e:
        print(f"Error loading high score: {e}")
    return 0

def save_highscore(email, score):
    try:
        doc_ref = db.collection('highscores').document(email)
        doc_ref.set({'score': score, 'email': email})
    except Exception as e:
        print(f"Error saving high score: {e}")

# Get user email and load high score
user_email = get_user_email()
highscore = load_highscore(user_email)

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

def run_game(mode):
    global highscore
    insert_count = 0  # For cheat code
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
                    pass  # Ignore window X button
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not paused:
                        bullet = player.shoot()
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                    elif event.key == pygame.K_ESCAPE:
                        paused = not paused
                    elif event.key == pygame.K_INSERT and mode == 'normal':
                        insert_count += 1
                        if insert_count == 5:
                            score = 1000
                            if mode == 'normal' and score >= 1000:
                                running = False
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
                    if mode == 'normal' and score >= 1000:
                        running = False

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

        # Check if normal mode completed
        if mode == 'normal' and score >= 1000:
            return 'star_wars_credits'

        # Save high score to Firestore
        save_highscore(user_email, highscore)

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
                    pass  # Ignore window X button
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

exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 50)
back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 60, 100, 40)

# Game mode select rects
normal_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 200, 200, 50)
endless_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 270, 200, 50)

# Credits section variable
credit_section = None

# Directions section variable
directions_section = None

# Star wars credits offset
star_wars_offset = 0

# Load texts
with open('directions.txt', 'r') as f:
    directions_text = f.read()
with open('credits.txt', 'r') as f:
    credits_text = f.read()
with open('Update Log.txt', 'r') as f:
    update_log_text = f.read()

# Prepare star wars credits text
star_wars_text = "Congratulations!\n\nYou have successfully completed Normal Mode by reaching a score of 1000!\n\n" + credits_text.replace('##', '').strip()

# Parse credits sections
credits_sections = []
with open('credits.txt', 'r') as f:
    lines = f.readlines()
current_section = None
current_content = []
for line in lines:
    line = line.strip()
    if line.startswith('##'):
        if current_section:
            credits_sections.append((current_section, '\n'.join(current_content)))
        current_section = line[2:].strip()  # Remove ##
        current_content = []
    elif current_section:
        current_content.append(line)
if current_section:
    credits_sections.append((current_section, '\n'.join(current_content)))

# Parse directions sections
directions_sections = []
with open('directions.txt', 'r') as f:
    lines = f.readlines()
current_section = None
current_content = []
for line in lines:
    line = line.strip()
    if line.startswith('##'):
        if current_section:
            directions_sections.append((current_section, '\n'.join(current_content)))
        current_section = line[2:].strip()
        current_content = []
    elif current_section:
        current_content.append(line)
if current_section:
    directions_sections.append((current_section, '\n'.join(current_content)))

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
        exit_text = font.render("Exit", True, WHITE)
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
        pygame.draw.rect(screen, WHITE, exit_rect, 2)
        screen.blit(exit_text, exit_text.get_rect(center=exit_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Ignore window X button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    current_screen = 'game_mode_select'
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
                elif exit_rect.collidepoint(event.pos):
                    save_highscore(user_email, highscore)
                    running = False

    elif current_screen == 'directions':
        screen.fill(BLACK)
        if directions_section is None:
            # Draw directions menu buttons dynamically
            button_rects = []
            for i, (title, _) in enumerate(directions_sections):
                text_render = font.render(title, True, WHITE)
                rect_width = text_render.get_width() + 40  # Add padding
                rect = pygame.Rect(SCREEN_WIDTH // 2 - rect_width // 2, 200 + i * 70, rect_width, 50)
                button_rects.append(rect)
                pygame.draw.rect(screen, WHITE, rect, 2)
                screen.blit(text_render, text_render.get_rect(center=rect.center))
            # Back to main menu
            back_text = font.render("Back", True, WHITE)
            pygame.draw.rect(screen, WHITE, back_rect, 2)
            screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        else:
            # Display the selected direction
            for title, content in directions_sections:
                if title == directions_section:
                    y = 200
                    for line in content.split('\n'):
                        if line.strip():
                            line_render = small_font.render(line, True, WHITE)
                            screen.blit(line_render, (SCREEN_WIDTH // 2 - line_render.get_width() // 2, y))
                            y += 30
                    break
            back_text = font.render("Back", True, WHITE)
            pygame.draw.rect(screen, WHITE, back_rect, 2)
            screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Ignore window X button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if directions_section is None:
                    for i, (title, _) in enumerate(directions_sections):
                        if button_rects[i].collidepoint(event.pos):
                            directions_section = title
                            break
                    if back_rect.collidepoint(event.pos):
                        current_screen = 'menu'
                else:
                    if back_rect.collidepoint(event.pos):
                        directions_section = None

    elif current_screen == 'credits':
        screen.fill(BLACK)
        if credit_section is None:
            # Draw credits menu buttons dynamically
            button_rects = []
            for i, (title, _) in enumerate(credits_sections):
                text_render = font.render(title, True, WHITE)
                rect_width = text_render.get_width() + 40  # Add padding
                rect = pygame.Rect(SCREEN_WIDTH // 2 - rect_width // 2, 200 + i * 70, rect_width, 50)
                button_rects.append(rect)
                pygame.draw.rect(screen, WHITE, rect, 2)
                screen.blit(text_render, text_render.get_rect(center=rect.center))
            # Back to main menu
            back_text = font.render("Back", True, WHITE)
            pygame.draw.rect(screen, WHITE, back_rect, 2)
            screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        else:
            # Display the selected credit
            for title, content in credits_sections:
                if title == credit_section:
                    y = 200
                    for line in content.split('\n'):
                        if line.strip():
                            line_render = small_font.render(line, True, WHITE)
                            screen.blit(line_render, (SCREEN_WIDTH // 2 - line_render.get_width() // 2, y))
                            y += 30
                    break
            back_text = font.render("Back", True, WHITE)
            pygame.draw.rect(screen, WHITE, back_rect, 2)
            screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Ignore window X button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if credit_section is None:
                    for i, (title, _) in enumerate(credits_sections):
                        if button_rects[i].collidepoint(event.pos):
                            credit_section = title
                            break
                    if back_rect.collidepoint(event.pos):
                        current_screen = 'menu'
                else:
                    if back_rect.collidepoint(event.pos):
                        credit_section = None

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
                pass  # Ignore window X button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    current_screen = 'menu'

    elif current_screen == 'game_mode_select':
        screen.fill(BLACK)
        title_text = font.render("Select Game Mode", True, WHITE)
        normal_text = font.render("Normal Mode", True, WHITE)
        endless_text = font.render("Endless Mode", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - 100, 100))
        pygame.draw.rect(screen, WHITE, normal_rect, 2)
        screen.blit(normal_text, normal_text.get_rect(center=normal_rect.center))
        pygame.draw.rect(screen, WHITE, endless_rect, 2)
        screen.blit(endless_text, endless_text.get_rect(center=endless_rect.center))
        back_text = font.render("Back", True, WHITE)
        pygame.draw.rect(screen, WHITE, back_rect, 2)
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Ignore window X button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if normal_rect.collidepoint(event.pos):
                    current_screen = 'game_normal'
                elif endless_rect.collidepoint(event.pos):
                    current_screen = 'game_endless'
                elif back_rect.collidepoint(event.pos):
                    current_screen = 'menu'

    elif current_screen == 'game_normal':
        result = run_game('normal')
        if result == 'quit':
            running = False
        elif result == 'star_wars_credits':
            star_wars_offset = 0
            current_screen = 'star_wars_credits'
        else:
            current_screen = result

    elif current_screen == 'game_endless':
        result = run_game('endless')
        if result == 'quit':
            running = False
        else:
            current_screen = result

    elif current_screen == 'star_wars_credits':
        screen.fill(BLACK)
        lines = star_wars_text.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                text_surf = small_font.render(line, True, YELLOW)
                y_pos = SCREEN_HEIGHT + i * 30 - star_wars_offset
                if 0 < y_pos < SCREEN_HEIGHT:
                    screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y_pos))
        star_wars_offset += 0.05
        if star_wars_offset > len(lines) * 30 + SCREEN_HEIGHT:
            current_screen = 'menu'
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Ignore window X button
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    current_screen = 'menu'

# Quit Pygame
pygame.quit()
sys.exit()