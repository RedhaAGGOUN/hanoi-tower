# /hanoi-tower/graphics.py
import pygame
import sys
import os
import random
import json

from solve import hanoi_solver
from utils import draw_text, ease_out_quad, Particle, TextInputBox

# --- Configuration & Colors ---
WIDTH, HEIGHT = 1280, 720
FPS = 60
WHITE, GOLD = (255, 255, 255), (255, 215, 0)
PRIMARY_BLUE, SECONDARY_BLUE = (29, 53, 87), (69, 123, 157)
STOP_RED = (217, 4, 41)
DISK_PALETTE = [(230, 57, 70), (241, 128, 45), (252, 192, 21), (168, 218, 220), (69, 123, 157), (29, 53, 87)]

# A helper class for cleaner state management
class StateManager:
    """Manages the current state of the application (e.g., menu, game)."""
    def __init__(self, app_instance):
        self.app = app_instance
        self.states = {}
        self.current_state_name = ''

    def register_state(self, name, state_instance):
        self.states[name] = state_instance

    def change_state(self, new_state_name, **kwargs):
        if self.current_state_name and self.states.get(self.current_state_name):
            self.states[self.current_state_name].on_exit()
        
        self.current_state_name = new_state_name
        if self.states.get(self.current_state_name):
            self.states[self.current_state_name].on_enter(**kwargs)

    def get_current_state(self):
        return self.states.get(self.current_state_name)

# Base class for all states (Menu, Game, Scoreboard, etc.)
class BaseState:
    """An abstract base class for different application states."""
    def __init__(self, app_instance):
        self.app = app_instance
        self.ui_buttons = {}

    def on_enter(self, **kwargs): pass
    def on_exit(self): pass
    def handle_event(self, event): pass
    def update(self, dt): pass
    def draw(self, screen): self.draw_credits(screen)

    def draw_buttons(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        for _, btn_data in self.ui_buttons.items():
            is_selected = btn_data.get('selected', False)
            base_color = btn_data.get('color', PRIMARY_BLUE if is_selected else SECONDARY_BLUE)
            color = tuple(min(255, c * 1.2) for c in base_color) if btn_data['rect'].collidepoint(mouse_pos) else base_color
            
            pygame.draw.rect(screen, color, btn_data['rect'], border_radius=10)
            pygame.draw.rect(screen, WHITE, btn_data['rect'], 3, border_radius=10)
            draw_text(screen, btn_data['text'], self.app.assets['font_ui'], WHITE, btn_data['rect'].centerx, btn_data['rect'].centery, centered=True)

    def draw_credits(self, screen):
        draw_text(screen, "Designed by Redha&Rooney@La Plateforme 07.2025", self.app.assets['font_credit'], (255, 255, 255, 150), WIDTH / 2, HEIGHT - 20, centered=True)

    def draw_frosted_overlay(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.blit(self.app.assets['blurred_background'], (0, 0))
        pygame.draw.rect(overlay, (0, 0, 0, 100), (0, 0, WIDTH, HEIGHT))
        screen.blit(overlay, (0, 0))


class HanoiGUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tours de Hanoï")
        self.clock = pygame.time.Clock()

        self.assets = {}
        self.sounds = {}
        self.scores = []
        self.player_name = ""

        self.state_manager = StateManager(self)
        self.register_states()
        
        self.load_assets()
        self.load_scoreboard()
        if pygame.mixer.get_init():
            pygame.mixer.music.play(-1)

        self.state_manager.change_state('menu')

    def register_states(self):
        self.state_manager.register_state('menu', MenuState(self))
        self.state_manager.register_state('get_name', GetNameState(self))
        self.state_manager.register_state('game', GameState(self))
        self.state_manager.register_state('win', WinState(self))
        self.state_manager.register_state('scoreboard', ScoreboardState(self))
        self.state_manager.register_state('how_to_play', HowToPlayState(self))
        self.state_manager.register_state('solver_explanation', SolverExplanationState(self))

    def load_assets(self):
        script_path = os.path.dirname(os.path.abspath(__file__))
        assets_path = os.path.join(script_path, 'assets')
        def asset(f): return os.path.join(assets_path, f)
        
        self.assets['background'] = pygame.transform.scale(pygame.image.load(asset('background.jpg')).convert(), (WIDTH, HEIGHT))
        logo_img = pygame.image.load(asset('logo.png')).convert_alpha()
        self.assets['logo'] = pygame.transform.scale(logo_img, (logo_img.get_width() // 2, logo_img.get_height() // 2))
        w, h = self.assets['background'].get_size()
        pixelated = pygame.transform.scale(self.assets['background'], (w // 20, h // 20))
        self.assets['blurred_background'] = pygame.transform.scale(pixelated, (w, h))
        self.assets['font_title'] = pygame.font.Font(asset('font.ttf'), 72)
        self.assets['font_menu'] = pygame.font.Font(asset('font.ttf'), 40)
        self.assets['font_ui'] = pygame.font.Font(asset('font.ttf'), 28)
        self.assets['font_credit'] = pygame.font.Font(asset('font.ttf'), 16)
        
        for name in ['pickup', 'drop', 'invalid', 'win']:
            self.sounds[name] = pygame.mixer.Sound(asset(f'{name}.wav'))
            self.sounds[name].set_volume(0.5)
        pygame.mixer.music.load(asset('background_music.mp3')); pygame.mixer.music.set_volume(0.3)

    def load_scoreboard(self):
        try:
            with open('scoreboard.json', 'r') as f: self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.scores = []

    def save_scoreboard(self):
        with open('scoreboard.json', 'w') as f: json.dump(self.scores, f, indent=4)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            current_state = self.state_manager.get_current_state()
            if not current_state:
                print("Error: No current state set. Exiting.")
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                current_state.handle_event(event)
            
            current_state.update(dt)
            current_state.draw(self.screen)
            pygame.display.flip()

# -- States --
class MenuState(BaseState):
    def on_enter(self, **kwargs):
        self.ui_buttons = {}
        w, h, g = 200, 70, 20
        # A more structured layout for disk selection buttons
        button_layout = {
            'disk_8': (1, 0), 'disk_7': (2, 0), 'disk_6': (0, 0),
            'disk_5': (2, 1), 'disk_4': (1, 1), 'disk_3': (0, 1),
        }
        grid_w = 3 * w + 2 * g
        start_x = (WIDTH - grid_w) / 2
        start_y = 350
        for name, (col, row) in button_layout.items():
            num_disks = int(name.split('_')[1])
            self.ui_buttons[name] = {
                'rect': pygame.Rect(start_x + col * (w + g), start_y + row * (h + g), w, h),
                'text': f'{num_disks} Disques',
                'action': (lambda n=num_disks: lambda: self.app.state_manager.change_state('get_name', num_disks=n))()
            }
        
        # Top-left info buttons
        self.ui_buttons['scoreboard'] = {'rect': pygame.Rect(30, 30, 200, 60), 'text': 'Scores', 'action': lambda: self.app.state_manager.change_state('scoreboard')}
        self.ui_buttons['how_to_play'] = {'rect': pygame.Rect(30, 100, 200, 60), 'text': 'Comment Jouer', 'action': lambda: self.app.state_manager.change_state('how_to_play')}
        self.ui_buttons['solver_explanation'] = {'rect': pygame.Rect(30, 170, 200, 60), 'text': 'Explication', 'action': lambda: self.app.state_manager.change_state('solver_explanation')}
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for _, btn in self.ui_buttons.items():
                if btn['rect'].collidepoint(event.pos):
                    self.app.sounds['drop'].play()
                    btn['action']()
                    break

    def draw(self, screen):
        screen.blit(self.app.assets['background'], (0, 0))
        draw_text(screen, "Tours de Hanoï", self.app.assets['font_title'], WHITE, WIDTH / 2, 150, centered=True)
        draw_text(screen, "Choisissez une difficulté", self.app.assets['font_menu'], GOLD, WIDTH / 2, 280, centered=True)
        self.draw_buttons(screen)
        screen.blit(self.app.assets['logo'], (WIDTH - self.app.assets['logo'].get_width() - 30, 30))
        super().draw(screen)

class GetNameState(BaseState):
    def on_enter(self, **kwargs):
        self.num_disks = kwargs.get('num_disks', 3)
        self.name_input = TextInputBox(WIDTH / 2 - 200, HEIGHT / 2 - 25, 400, 60, self.app.assets['font_menu'], self.app.player_name)
        # To draw the menu in the background
        self.menu_state_instance = self.app.state_manager.states['menu']
        self.menu_state_instance.on_enter()

    def handle_event(self, event):
        if self.name_input and self.name_input.handle_event(event) == 'enter':
            player_name = self.name_input.text.strip()
            if player_name:
                self.app.player_name = player_name
                self.app.sounds['drop'].play()
                self.app.state_manager.change_state('game', num_disks=self.num_disks)

    def update(self, dt):
        if self.name_input:
            self.name_input.update()
            
    def draw(self, screen):
        self.menu_state_instance.draw(screen)
        self.draw_frosted_overlay(screen)
        draw_text(screen, "Entrez votre nom", self.app.assets['font_title'], GOLD, WIDTH / 2, HEIGHT / 2 - 100, centered=True)
        if self.name_input: self.name_input.draw(screen)
        draw_text(screen, "Appuyez sur Entrée pour commencer", self.app.assets['font_ui'], WHITE, WIDTH / 2, HEIGHT / 2 + 100, centered=True)

class GameState(BaseState):
    def on_enter(self, **kwargs):
        self.n = kwargs.get('num_disks', 3)
        self.min_moves = (2 ** self.n) - 1
        self.moves = 0
        self.start_time = pygame.time.get_ticks()
        self.dragging_disk = None
        self.source_tower_idx = -1
        self.animating = False

        self.towers = [[] for _ in range(3)]
        self.disks = []
        base_w, h = 50, 25
        for i in range(self.n, 0, -1):
            disk = {'size': i, 'color': DISK_PALETTE[i % len(DISK_PALETTE)], 'rect': pygame.Rect(0, 0, base_w + i * 20, h), 'pos': pygame.Vector2(0, 0)}
            self.disks.append(disk); self.towers[0].append(disk)

        base_r = pygame.Rect(WIDTH * 0.1, HEIGHT - 200, WIDTH * 0.8, 40)
        self.tower_rects = [
            pygame.Rect(base_r.centerx / 2, base_r.top - 300, 20, 300),
            pygame.Rect(base_r.centerx, base_r.top - 300, 20, 300),
            pygame.Rect(base_r.centerx * 1.5, base_r.top - 300, 20, 300)]
        self.reset_disk_positions()
        
        btn_w, btn_h = 170, 50
        self.ui_buttons = {
            'solve': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 2 - 40, btn_w, btn_h), 'text': 'Solution', 'action': self.start_animation},
            'back': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h - 30, btn_w, btn_h), 'text': 'Menu', 'action': lambda: self.app.state_manager.change_state('menu')},
            'solver_explanation': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 3 - 60, btn_w, btn_h), 'text': 'Explication', 'action': lambda: self.app.state_manager.change_state('solver_explanation')}
        }
    
    def handle_event(self, event):
        if self.animating: return
        
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.dragging_disk: return

            for name, btn in self.ui_buttons.items():
                if btn['rect'].collidepoint(mouse_pos):
                    self.app.sounds['drop'].play()
                    btn['action']()
                    return

            for i, tower in enumerate(self.towers):
                if tower and tower[-1]['rect'].collidepoint(mouse_pos):
                    self.source_tower_idx, self.dragging_disk = i, tower.pop()
                    self.app.sounds['pickup'].play()
                    return

        if event.type == pygame.MOUSEMOTION and self.dragging_disk:
            self.dragging_disk['pos'] = pygame.Vector2(mouse_pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging_disk:
            target_idx = self.get_tower_at(mouse_pos)
            is_valid = target_idx is not None and (not self.towers[target_idx] or self.dragging_disk['size'] < self.towers[target_idx][-1]['size'])
            
            if is_valid:
                self.towers[target_idx].append(self.dragging_disk)
                if self.source_tower_idx != target_idx: self.moves += 1
                self.app.sounds['drop'].play()
            else:
                self.towers[self.source_tower_idx].append(self.dragging_disk)
                if target_idx is not None: self.app.sounds['invalid'].play()
            
            self.dragging_disk = None
            self.reset_disk_positions()
            if len(self.towers[1]) == self.n or len(self.towers[2]) == self.n:
                self.trigger_win()
                
    def draw(self, screen):
        screen.blit(self.app.assets['background'], (0, 0))
        self.draw_scenery(screen)
        self.draw_disks(screen)
        self.draw_buttons(screen)
        screen.blit(self.app.assets['logo'], (WIDTH - self.app.assets['logo'].get_width() - 30, 30))
        
        draw_text(screen, f"Mouvements: {self.moves}", self.app.assets['font_ui'], WHITE, 40, 40)
        draw_text(screen, f"Minimum: {self.min_moves}", self.app.assets['font_ui'], GOLD, 40, 80)
        
        if not self.animating:
            elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
            minutes, seconds = divmod(elapsed_time, 60)
            draw_text(screen, f"Temps: {int(minutes):02}:{int(seconds):02}", self.app.assets['font_ui'], WHITE, 40, 120)
        super().draw(screen)

    def draw_scenery(self, screen):
        base = pygame.Rect(WIDTH * 0.1, HEIGHT - 200, WIDTH * 0.8, 40)
        pygame.draw.rect(screen, (30, 30, 30), base, border_top_left_radius=10, border_top_right_radius=10)
        for t in self.tower_rects: pygame.draw.rect(screen, (80, 80, 80), t, border_radius=5)
    
    def draw_disks(self, screen, disks_to_draw=None, disk_in_motion=None):
        if disks_to_draw is None: disks_to_draw = self.disks
        for disk in disks_to_draw:
            if disk != self.dragging_disk and disk != disk_in_motion:
                self.draw_single_disk(screen, disk)
        # Draw moving disk last so it's on top
        if self.dragging_disk: self.draw_single_disk(screen, self.dragging_disk)
        if disk_in_motion: self.draw_single_disk(screen, disk_in_motion)
            
    def draw_single_disk(self, screen, disk):
        color = disk.get('color', (128, 128, 128))
        disk['rect'].center = disk['pos']
        pygame.draw.rect(screen, color, disk['rect'], border_radius=5)
        border_color = [min(255, int(c * 0.8)) for c in color]
        pygame.draw.rect(screen, border_color, disk['rect'], 3, border_radius=5)

    def reset_disk_positions(self, towers=None):
        target_towers = towers if towers is not None else self.towers
        for i, tower in enumerate(target_towers):
            for j, disk in enumerate(tower):
                disk['pos'] = pygame.Vector2(self.tower_rects[i].centerx, self.tower_rects[i].bottom - j * disk['rect'].height)
    
    def get_tower_at(self, pos):
        for i, t in enumerate(self.tower_rects):
            if t.inflate(100, 400).collidepoint(pos): return i
        return None

    def start_animation(self):
        if self.animating: return
        self.animating = True
        
        # Start a temporary solver that will take control of the screen
        AnimationSolver(self.app, self, on_finish=self.on_animation_finish)
    
    def on_animation_finish(self, final_towers, final_disks, final_moves):
        self.animating = False
        self.towers, self.disks, self.moves = final_towers, final_disks, final_moves
        self.reset_disk_positions()
        # Re-establish normal buttons after animation
        btn_w, btn_h = 170, 50
        self.ui_buttons = {
            'solve': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 2 - 40, btn_w, btn_h), 'text': 'Solution', 'action': self.start_animation},
            'back': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h - 30, btn_w, btn_h), 'text': 'Menu', 'action': lambda: self.app.state_manager.change_state('menu')},
            'solver_explanation': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 3 - 60, btn_w, btn_h), 'text': 'Explication', 'action': lambda: self.app.state_manager.change_state('solver_explanation')}
        }
        self.trigger_win()

    def trigger_win(self):
        time_taken = (pygame.time.get_ticks() - self.start_time) / 1000
        win_tower_idx = 1 if len(self.towers[1]) == self.n else 2
        
        self.app.state_manager.change_state('win',
                                           moves=self.moves,
                                           min_moves=self.min_moves,
                                           time_taken=time_taken,
                                           num_disks=self.n,
                                           player_name=self.app.player_name,
                                           win_tower_pos=self.tower_rects[win_tower_idx].center)

class WinState(BaseState):
    def on_enter(self, **kwargs):
        self.moves, self.min_moves = kwargs['moves'], kwargs['min_moves']
        self.num_disks, self.player_name = kwargs['num_disks'], kwargs['player_name']
        win_tower_pos = kwargs['win_tower_pos']
        
        self.app.sounds['win'].play()
        # Add a new score to the global scores list
        self.app.scores.append({'name': self.player_name, 'disks': self.num_disks, 'time': kwargs['time_taken'], 'moves': self.moves})
        self.app.save_scoreboard()
        
        # Create particles for confetti effect
        self.particles = [Particle(win_tower_pos[0], win_tower_pos[1], random.choice(DISK_PALETTE)) for _ in range(150)]
        self.game_state_instance = self.app.state_manager.states['game']
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            self.app.state_manager.change_state('scoreboard', highlight_difficulty=self.num_disks)

    def update(self, dt):
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        
    def draw(self, screen):
        # Draw the final game state in the background
        self.game_state_instance.draw(screen)
        self.draw_frosted_overlay(screen)
        
        for p in self.particles: p.draw(screen)
            
        message = "Parfait !" if self.moves <= self.min_moves else "Bravo !"
        draw_text(screen, message, self.app.assets['font_title'], GOLD, WIDTH / 2, HEIGHT / 2 - 100, centered=True)
        draw_text(screen, f"{self.player_name}, vous avez gagné !", self.app.assets['font_menu'], WHITE, WIDTH / 2, HEIGHT / 2, centered=True)
        draw_text(screen, "Appuyez pour voir les scores", self.app.assets['font_ui'], WHITE, WIDTH / 2, HEIGHT / 2 + 100, centered=True)

class ScoreboardState(BaseState):
    def on_enter(self, **kwargs):
        game_state = self.app.state_manager.states.get('game')
        default_n = game_state.n if game_state and game_state.n else 5
        self.selected_difficulty = kwargs.get('highlight_difficulty', default_n)
        
        self.ui_buttons = {}
        y, w, h, g = 150, 120, 50, 10
        total_w = 6 * (w + g) - g; start_x = (WIDTH - total_w) / 2
        
        for i in range(3, 9):
            self.ui_buttons[f'score_{i}'] = {
                'rect': pygame.Rect(start_x + (i - 3) * (w + g), y, w, h),
                'text': f'{i} Disques',
                'action': (lambda n=i: lambda: self.set_difficulty(n))(),
                'selected': i == self.selected_difficulty
            }
        self.ui_buttons['back_menu'] = {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Menu', 'action': lambda: self.app.state_manager.change_state('menu')}

    def set_difficulty(self, num):
        for btn in self.ui_buttons.values(): btn['selected'] = False
        self.selected_difficulty = num
        if f'score_{num}' in self.ui_buttons: self.ui_buttons[f'score_{num}']['selected'] = True
            
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.ui_buttons.values():
                if btn['rect'].collidepoint(event.pos):
                    self.app.sounds['drop'].play(); btn['action'](); break

    def draw(self, screen):
        screen.blit(self.app.assets['background'], (0, 0))
        self.draw_frosted_overlay(screen)
        draw_text(screen, "Tableau des Scores", self.app.assets['font_title'], GOLD, WIDTH / 2, 70, centered=True)
        self.draw_buttons(screen)
        
        headers = ["Rang", "Nom", "Mouvements", "Temps"]
        for i, header in enumerate(headers):
            draw_text(screen, header, self.app.assets['font_ui'], GOLD, 150 + i * 250, 250)
            
        filtered_scores = sorted([s for s in self.app.scores if s.get('disks') == self.selected_difficulty], key=lambda s: (s.get('moves', 999), s.get('time', 999)))
        for i, score in enumerate(filtered_scores[:10]):
            y = 300 + i * 40
            time_val = score.get('time', 0); minutes, seconds = divmod(time_val, 60)
            time_str = f"{int(minutes):02}:{seconds:05.2f}"
            data = [f"#{i+1}", score.get('name', '???'), str(score.get('moves', '-')), time_str]
            for j, item in enumerate(data):
                draw_text(screen, item, self.app.assets['font_ui'], WHITE, 150 + j * 250, y)

class HowToPlayState(BaseState):
    def on_enter(self, **kwargs):
        self.ui_buttons = {'back_menu': {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Retour', 'action': lambda: self.app.state_manager.change_state('menu')}}
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ui_buttons['back_menu']['rect'].collidepoint(event.pos):
                self.app.sounds['drop'].play(); self.ui_buttons['back_menu']['action']()

    def draw(self, screen):
        screen.blit(self.app.assets['background'], (0, 0))
        self.draw_frosted_overlay(screen)
        draw_text(screen, "Comment Jouer", self.app.assets['font_title'], GOLD, WIDTH / 2, 100, centered=True)
        instructions = ["Le but est de déplacer tous les disques de la tour de gauche", "vers une autre tour, en respectant ces règles :", "", "1. Déplacez un disque à la fois en le cliquant-glissant.", "2. Un disque plus grand ne peut pas être posé sur un plus petit.", "", "Essayez de le faire avec le moins de mouvements possible !"]
        for i, line in enumerate(instructions):
            draw_text(screen, line, self.app.assets['font_ui'], WHITE, WIDTH / 2, 220 + i * 45, centered=True)
        self.draw_buttons(screen); super().draw(screen)

class SolverExplanationState(BaseState):
    def on_enter(self, **kwargs):
        self.ui_buttons = {'back_menu': {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Retour', 'action': lambda: self.app.state_manager.change_state('menu')}}
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ui_buttons['back_menu']['rect'].collidepoint(event.pos):
                self.app.sounds['drop'].play(); self.ui_buttons['back_menu']['action']()
    def draw(self, screen):
        screen.blit(self.app.assets['background'], (0, 0))
        self.draw_frosted_overlay(screen)
        draw_text(screen, "Explication du Solveur", self.app.assets['font_title'], GOLD, WIDTH / 2, 50, centered=True)
        explanation = ["Le problème est résolu par une approche récursive.", "Pour 'n' disques de la Source à la Destination :", "1. Déplacer (n-1) disques de Source vers Auxiliaire.", "2. Déplacer le plus grand disque de Source vers Destination.", "3. Déplacer les (n-1) disques de Auxiliaire vers Destination.", "", "Le nombre minimum de mouvements est donné par la formule : 2ⁿ - 1."]
        for i, line in enumerate(explanation):
            draw_text(screen, line, self.app.assets['font_ui'], WHITE, WIDTH / 2, 180 + i * 45, centered=True)
        self.draw_buttons(screen); super().draw(screen)

# -- Animation Class --
class AnimationSolver:
    """A temporary class to handle the animation sequence."""
    def __init__(self, app, game_state, on_finish):
        self.app, self.game, self.on_finish = app, game_state, on_finish
        self.solution = hanoi_solver(self.game.n, 0, 2, 1)
        self.towers, self.disks = [list(t) for t in self.game.towers], [dict(d) for d in self.game.disks]
        self.move_index, self.progress, self.duration = 0, 0, 0.4
        self.current_disk = self.start_pos = self.end_pos = self.mid_pos = None
        self.game.ui_buttons = {'stop': {'rect': self.game.ui_buttons['solve']['rect'], 'text': 'Arrêter', 'color': STOP_RED}}
        self.start_next_move()

    def start_next_move(self):
        if self.move_index >= len(self.solution):
            self.on_finish(self.towers, self.disks, len(self.solution))
            # Override self to prevent further updates after finishing
            self.update = lambda dt: None; self.draw = lambda screen: None; self.handle_event = lambda event: None
            return

        self.progress = 0
        src, dest = self.solution[self.move_index]
        self.current_disk = self.towers[src].pop()
        self.start_pos = self.current_disk['pos'].copy()
        self.mid_pos = pygame.Vector2((self.game.tower_rects[src].centerx + self.game.tower_rects[dest].centerx) / 2, 150)
        self.end_pos = pygame.Vector2(self.game.tower_rects[dest].centerx, self.game.tower_rects[dest].bottom - (len(self.towers[dest]) * self.current_disk['rect'].height))
        self.move_index += 1
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.game.ui_buttons['stop']['rect'].collidepoint(event.pos):
                self.app.sounds['invalid'].play(); self.on_finish(self.game.towers, self.game.disks, self.game.moves)

    def update(self, dt):
        self.progress += dt / self.duration
        if self.progress >= 1: self.start_next_move()
        else:
            t = ease_out_quad(self.progress)
            self.current_disk['pos'] = self.start_pos.lerp(self.mid_pos, t * 2) if t < 0.5 else self.mid_pos.lerp(self.end_pos, (t - 0.5) * 2)

    def draw(self, screen):
        original_handler = self.app.state_manager.get_current_state().draw
        if original_handler and original_handler != self.draw:
            # Draw the background game screen first
            self.app.screen.blit(self.app.assets['background'], (0, 0))
            self.game.draw_scenery(screen)
            self.game.draw_buttons(screen) # Draw 'stop' button
            # Now draw the animated disks
            all_disks = [d for t in self.towers for d in t] + [self.current_disk]
            self.game.draw_disks(screen, disks_to_draw=all_disks)