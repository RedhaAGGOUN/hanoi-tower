import pygame
import sys
import os
import random
import json
import math
import uuid

from solve import hanoi_solver
from utils import draw_text, ease_out_quad, Particle, TextInputBox

# --- Configuration & Colors ---
WIDTH, HEIGHT = 1280, 720
FPS = 60
WHITE = (255, 255, 255); GOLD = (255, 215, 0); PRIMARY_BLUE = (0, 91, 181)
SECONDARY_BLUE = (69, 123, 157); STOP_RED = (217, 4, 41)
DISK_PALETTE = [
    (230, 57, 70), (241, 128, 45), (252, 192, 21),
    (168, 218, 220), (69, 123, 157), (29, 53, 87)
]

class HanoiGUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tours de Hanoï")
        self.clock = pygame.time.Clock()

        # Initialize all attributes to default values before use
        self.game_state = ''
        self.scores = []
        self.particles = []
        self.ui_buttons = {}
        self.animating = False
        self.dragging_disk = None
        self.source_tower_idx = -1
        self.player_name = ""
        self.start_time = 0
        self.towers = []
        self.disks = []
        self.tower_rects = []
        self.n = 0
        self.min_moves = 0
        self.selected_score_difficulty = 5
        self.pending_disks = 0
        self.name_input = None
        self.is_solver_used = False  # Track if solver was used
        self.move_history = []  # Track moves in current game
        self.game_id = str(uuid.uuid4())  # Unique ID for current game

        try:
            self.load_assets()
            self.load_scoreboard()
            self.load_move_history()
            self.setup_menu()  # Set the initial state
            if pygame.mixer.get_init():
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Initialization error: {e}")
            with open("error.log", "a") as f:
                f.write(f"Initialization error: {str(e)}\n")
            raise

    def load_assets(self):
        script_path = os.path.dirname(os.path.abspath(__file__))
        assets_path = os.path.join(script_path, 'assets')
        def asset(f): return os.path.join(assets_path, f)
        try:
            self.background_img = pygame.transform.scale(pygame.image.load(asset('background.jpg')).convert(), (WIDTH, HEIGHT))
            logo = pygame.image.load(asset('logo.png')).convert_alpha()
            self.logo_img = pygame.transform.scale(logo, (logo.get_width() // 2, logo.get_height() // 2))  # Scale to 85x25
            w, h = self.background_img.get_size()
            pixelated = pygame.transform.scale(self.background_img, (w // 20, h // 20))
            self.blurred_background = pygame.transform.scale(pixelated, (w, h))
            self.title_font = pygame.font.Font(asset('font.ttf'), 72)
            self.menu_font = pygame.font.Font(asset('font.ttf'), 40)
            self.ui_font = pygame.font.Font(asset('font.ttf'), 28)
            self.credit_font = pygame.font.Font(asset('font.ttf'), 16)  # New smaller font for credits
            self.sounds = {
                'pickup': pygame.mixer.Sound(asset('pickup.wav')), 'drop': pygame.mixer.Sound(asset('drop.wav')),
                'invalid': pygame.mixer.Sound(asset('invalid.wav')), 'win': pygame.mixer.Sound(asset('win.wav'))
            }
            for sound in self.sounds.values(): sound.set_volume(0.5)
            pygame.mixer.music.load(asset('background_music.mp3')); pygame.mixer.music.set_volume(0.3)
        except (pygame.error, FileNotFoundError) as e:
            raise RuntimeError(f"FATAL: Asset non trouvé. Vérifiez '{os.path.abspath(assets_path)}'. Erreur: {e}") from e

    def load_scoreboard(self):
        try:
            with open('scoreboard.json', 'r') as f: self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.scores = []

    def load_move_history(self):
        try:
            with open('move_history.json', 'r') as f: self.full_move_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.full_move_history = []

    def save_scoreboard(self):
        try:
            with open('scoreboard.json', 'w') as f: json.dump(self.scores, f, indent=4)
        except Exception as e:
            print(f"Error saving scoreboard: {e}")
            with open("error.log", "a") as f:
                f.write(f"save_scoreboard error: {str(e)}\n")

    def save_move_history(self):
        try:
            with open('move_history.json', 'w') as f: json.dump(self.full_move_history, f, indent=4)
        except Exception as e:
            print(f"Error saving move history: {e}")
            with open("error.log", "a") as f:
                f.write(f"save_move_history error: {str(e)}\n")

    def run(self):
        while True:
            self.clock.tick(FPS)
            
            try:
                # 1. Handle Events for the current state
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    
                    # Dynamically call the correct event handler
                    handler = getattr(self, f'handle_{self.game_state}_events', self.handle_null_events)
                    handler(event)

                # 2. Draw the current state
                drawer = getattr(self, f'draw_{self.game_state}', self.draw_null_state)
                drawer()
            except Exception as e:
                print(f"Error in main loop: {e}")
                with open("error.log", "a") as f:
                    f.write(f"Main loop error: {str(e)}, game_state={self.game_state}, n={self.n}, towers={self.towers}\n")
                raise

            pygame.display.flip()
    
    def handle_null_events(self, event):
        pass # A safe fallback event handler

    def draw_null_state(self):
        self.screen.fill((0,0,0)) # A safe fallback drawer
        draw_text(self.screen, "Error: Invalid State", self.title_font, WHITE, WIDTH/2, HEIGHT/2, centered=True)

    # --- STATE SETUP ---
    def setup_menu(self):
        try:
            self.game_state = 'menu'
            self.ui_buttons = {}
            w, h, g = 200, 70, 20
            # Top button: 8 disks
            self.ui_buttons['disk_8'] = {'rect': pygame.Rect((WIDTH - w) / 2, 300, w, h), 'text': '8 Disques'}
            # Middle row: 6 and 7 disks
            self.ui_buttons['disk_6'] = {'rect': pygame.Rect((WIDTH - w * 2 - g) / 2, 390, w, h), 'text': '6 Disques'}
            self.ui_buttons['disk_7'] = {'rect': pygame.Rect((WIDTH + g) / 2, 390, w, h), 'text': '7 Disques'}
            # Bottom row: 3, 4, 5 disks
            self.ui_buttons['disk_3'] = {'rect': pygame.Rect((WIDTH - w * 3 - g * 2) / 2, 480, w, h), 'text': '3 Disques'}
            self.ui_buttons['disk_4'] = {'rect': pygame.Rect((WIDTH - w) / 2, 480, w, h), 'text': '4 Disques'}
            self.ui_buttons['disk_5'] = {'rect': pygame.Rect((WIDTH + w + g * 2) / 2, 480, w, h), 'text': '5 Disques'}
            # Top-left: Scores, How to Play, and Solver Explanation
            self.ui_buttons['scoreboard'] = {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Scores'}
            self.ui_buttons['how_to_play'] = {'rect': pygame.Rect(30, 100, 150, 60), 'text': 'Comment?'}
            self.ui_buttons['solver?'] = {'rect': pygame.Rect(30, 170, 150, 60), 'text': 'Solveur?'}
        except Exception as e:
            print(f"Error in setup_menu: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_menu error: {str(e)}\n")
            raise

    def setup_get_name(self, num_disks):
        try:
            self.game_state = 'get_name'
            self.pending_disks = max(1, num_disks)  # Ensure at least 1 disk
            self.name_input = TextInputBox(WIDTH / 2 - 200, HEIGHT / 2 - 25, 400, 60, self.menu_font, self.player_name)
            self.move_history = []  # Reset move history for new game
            self.game_id = str(uuid.uuid4())  # New game ID
        except Exception as e:
            print(f"Error in setup_get_name: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_get_name error: {str(e)}, num_disks={num_disks}, player_name={self.player_name}\n")
            raise

    def setup_game(self, num_disks):
        try:
            self.game_state = 'game'
            self.n = max(1, num_disks)  # Ensure at least 1 disk
            if self.n > 8:  # Cap at 8 to match UI buttons
                print(f"Number of disks capped at 8: requested {self.n}")
                self.n = 8
            self.min_moves = (2**self.n) - 1
            self.moves, self.animating = 0, False
            self.towers = [[] for _ in range(3)]; self.disks = []
            self.dragging_disk = None
            self.is_solver_used = False  # Reset solver flag
            base_w, h = 50, 25
            if not DISK_PALETTE:
                raise ValueError("DISK_PALETTE is empty")
            for i in range(self.n, 0, -1):
                disk = {'size': i, 'color': DISK_PALETTE[i % len(DISK_PALETTE)], 'rect': pygame.Rect(0, 0, base_w + i * 20, h), 'pos': pygame.Vector2(0, 0)}
                self.disks.append(disk); self.towers[0].append(disk)
            base_r = pygame.Rect(WIDTH * 0.1, HEIGHT - 200, WIDTH * 0.8, 40)
            self.tower_rects = [
                pygame.Rect(base_r.centerx / 2, base_r.top - 300, 20, 300),
                pygame.Rect(base_r.centerx, base_r.top - 300, 20, 300),
                pygame.Rect(base_r.centerx * 1.5, base_r.top - 300, 20, 300)
            ]
            self.reset_disk_positions()
            btn_w, btn_h = 170, 50
            self.ui_buttons = {
                'solve': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 3 - 60, btn_w, btn_h), 'text': 'Solution'},
                'history': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 2 - 40, btn_w, btn_h), 'text': 'Historique'},
                'back': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h - 30, btn_w, btn_h), 'text': 'Menu'},
                'solver_explanation': {'rect': pygame.Rect(WIDTH - btn_w - 30, HEIGHT - btn_h * 4 - 80, btn_w, btn_h), 'text': 'Solveur?'}
            }
            self.start_time = pygame.time.get_ticks()
        except Exception as e:
            print(f"Error in setup_game: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_game error: {str(e)}, num_disks={num_disks}, n={self.n}, towers={self.towers}\n")
            raise

    def setup_scoreboard(self):
        try:
            self.game_state = 'scoreboard'
            self.ui_buttons = {}
            self.selected_score_difficulty = getattr(self, 'n', 5)
            y, w, h, g = 150, 120, 50, 10; total_w = 6 * (w + g) - g
            start_x = (WIDTH - total_w) / 2
            for i in range(3, 9):
                self.ui_buttons[f'score_{i}'] = {'rect': pygame.Rect(start_x + (i - 3) * (w + g), y, w, h), 'text': f'{i} Disques'}
            self.ui_buttons['back_menu'] = {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Menu'}
        except Exception as e:
            print(f"Error in setup_scoreboard: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_scoreboard error: {str(e)}, selected_score_difficulty={self.selected_score_difficulty}\n")
            raise

    def setup_how_to_play(self):
        try:
            self.game_state = 'how_to_play'
            self.ui_buttons = {}
            self.ui_buttons['back_menu'] = {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Retour'}
        except Exception as e:
            print(f"Error in setup_how_to_play: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_how_to_play error: {str(e)}\n")
            raise

    def setup_solver_explanation(self):
        try:
            self.game_state = 'solver_explanation'
            self.ui_buttons = {
                'back_menu': {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Retour'}
            }
        except Exception as e:
            print(f"Error in setup_solver_explanation: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_solver_explanation error: {str(e)}\n")
            raise

    def setup_history(self):
        try:
            self.game_state = 'history'
            self.ui_buttons = {
                'back_menu': {'rect': pygame.Rect(30, 30, 150, 60), 'text': 'Retour'}
            }
        except Exception as e:
            print(f"Error in setup_history: {e}")
            with open("error.log", "a") as f:
                f.write(f"setup_history error: {str(e)}\n")
            raise

    # --- EVENT HANDLERS ---
    def handle_menu_events(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, btn in self.ui_buttons.items():
                    if btn['rect'].collidepoint(event.pos):
                        self.sounds['drop'].play()
                        if 'disk' in name: self.setup_get_name(int(name.split('_')[1]))
                        elif name == 'scoreboard': self.setup_scoreboard()
                        elif name == 'how_to_play': self.setup_how_to_play()
                        elif name == 'solver_explanation': self.setup_solver_explanation()
        except Exception as e:
            print(f"Error in handle_menu_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_menu_events error: {str(e)}, ui_buttons={self.ui_buttons}\n")
            raise

    def handle_get_name_events(self, event):
        try:
            if self.name_input and self.name_input.handle_event(event) == 'enter' and len(self.name_input.text.strip()) > 0:
                self.player_name = self.name_input.text.strip()
                self.sounds['drop'].play()
                self.setup_game(self.pending_disks)
        except Exception as e:
            print(f"Error in handle_get_name_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_get_name_events error: {str(e)}, pending_disks={self.pending_disks}\n")
            raise

    def handle_game_events(self, event):
        if self.animating: return
        try:
            mouse_pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.dragging_disk:
                    if self.ui_buttons.get('back') and self.ui_buttons['back']['rect'].collidepoint(mouse_pos):
                        self.sounds['drop'].play(); self.setup_menu(); return
                    if self.ui_buttons.get('solve') and self.ui_buttons['solve']['rect'].collidepoint(mouse_pos):
                        self.sounds['drop'].play(); self.start_animation(); return
                    if self.ui_buttons.get('history') and self.ui_buttons['history']['rect'].collidepoint(mouse_pos):
                        self.sounds['drop'].play(); self.setup_history(); return
                    if self.ui_buttons.get('solver_explanation') and self.ui_buttons['solver_explanation']['rect'].collidepoint(mouse_pos):
                        self.sounds['drop'].play(); self.setup_solver_explanation(); return
                    for i, tower in enumerate(self.towers):
                        if tower and tower[-1]['rect'].collidepoint(mouse_pos):
                            self.source_tower_idx = i
                            self.dragging_disk = self.towers[i].pop()
                            self.sounds['pickup'].play(); return
            if event.type == pygame.MOUSEMOTION and self.dragging_disk:
                self.dragging_disk['pos'] = pygame.Vector2(mouse_pos)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging_disk:
                target_idx = self.get_tower_at(mouse_pos)
                if target_idx is not None and not (0 <= target_idx < len(self.towers)):
                    print(f"Invalid target_idx: {target_idx}")
                    with open("error.log", "a") as f:
                        f.write(f"Invalid target_idx in handle_game_events: {target_idx}, towers={self.towers}, source_tower_idx={self.source_tower_idx}\n")
                    self.towers[self.source_tower_idx].append(self.dragging_disk)
                    self.sounds['invalid'].play()
                    self.dragging_disk = None; self.reset_disk_positions()
                    return
                is_valid = target_idx is not None and (not self.towers[target_idx] or self.dragging_disk['size'] < self.towers[target_idx][-1]['size'])
                if is_valid:
                    self.towers[target_idx].append(self.dragging_disk)
                    if self.source_tower_idx != target_idx:
                        self.moves += 1
                        self.move_history.append({'source': self.source_tower_idx + 1, 'destination': target_idx + 1})
                    self.sounds['drop'].play()
                else:
                    self.towers[self.source_tower_idx].append(self.dragging_disk)
                    if target_idx is not None: self.sounds['invalid'].play()
                self.dragging_disk = None; self.reset_disk_positions(); self.check_win()
        except Exception as e:
            print(f"Error in handle_game_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_game_events error: {str(e)}, state: n={self.n}, towers={self.towers}, target_idx={target_idx if 'target_idx' in locals() else 'undefined'}\n")
            self.sounds['invalid'].play()
            self.dragging_disk = None
            self.reset_disk_positions()

    def handle_win_events(self, event):
        try:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1): self.setup_scoreboard()
        except Exception as e:
            print(f"Error in handle_win_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_win_events error: {str(e)}\n")
            raise

    def handle_scoreboard_events(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, btn in self.ui_buttons.items():
                    if btn['rect'].collidepoint(event.pos):
                        self.sounds['drop'].play()
                        if 'score_' in name: self.selected_score_difficulty = int(name.split('_')[1])
                        elif name == 'back_menu': self.setup_menu()
        except Exception as e:
            print(f"Error in handle_scoreboard_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_scoreboard_events error: {str(e)}, ui_buttons={self.ui_buttons}\n")
            raise

    def handle_how_to_play_events(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, btn in self.ui_buttons.items():
                    if btn['rect'].collidepoint(event.pos) and name == 'back_menu':
                        self.sounds['drop'].play()
                        self.setup_menu()
        except Exception as e:
            print(f"Error in handle_how_to_play_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_how_to_play_events error: {str(e)}, ui_buttons={self.ui_buttons}\n")
            raise

    def handle_solver_explanation_events(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, btn in self.ui_buttons.items():
                    if btn['rect'].collidepoint(event.pos) and name == 'back_menu':
                        self.sounds['drop'].play()
                        self.setup_menu()
        except Exception as e:
            print(f"Error in handle_solver_explanation_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_solver_explanation_events error: {str(e)}, ui_buttons={self.ui_buttons}\n")
            raise

    def handle_history_events(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, btn in self.ui_buttons.items():
                    if btn['rect'].collidepoint(event.pos) and name == 'back_menu':
                        self.sounds['drop'].play()
                        self.setup_menu()
        except Exception as e:
            print(f"Error in handle_history_events: {e}")
            with open("error.log", "a") as f:
                f.write(f"handle_history_events error: {str(e)}, ui_buttons={self.ui_buttons}\n")
            raise

    # --- DRAWING FUNCTIONS ---
    def draw_menu(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            draw_text(self.screen, "Tours de Hanoï", self.title_font, WHITE, WIDTH / 2, 150, centered=True)
            draw_text(self.screen, "Choisissez une difficulté", self.menu_font, GOLD, WIDTH / 2, 220, centered=True)
            self.draw_buttons(self.ui_buttons)
            self.screen.blit(self.logo_img, (WIDTH - self.logo_img.get_width() - 30, 30))  # Logo top-right
            self.draw_credits()
        except Exception as e:
            print(f"Error in draw_menu: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_menu error: {str(e)}\n")
            raise

    def draw_get_name(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            self.draw_frosted_overlay()
            draw_text(self.screen, "Entrez votre nom", self.title_font, GOLD, WIDTH / 2, HEIGHT / 2 - 100, centered=True)
            if self.name_input: self.name_input.update(); self.name_input.draw(self.screen)
            draw_text(self.screen, "Appuyez sur Entrée pour commencer", self.ui_font, WHITE, WIDTH / 2, HEIGHT / 2 + 100, centered=True)
        except Exception as e:
            print(f"Error in draw_get_name: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_get_name error: {str(e)}\n")
            raise

    def draw_game(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            self.draw_scenery(); self.draw_disks(); self.draw_buttons(self.ui_buttons)
            self.screen.blit(self.logo_img, (WIDTH - self.logo_img.get_width() - 30, 30))
            draw_text(self.screen, f"Mouvements: {self.moves}", self.ui_font, WHITE, 40, 40)
            draw_text(self.screen, f"Minimum: {self.min_moves}", self.ui_font, GOLD, 40, 80)
            if not self.animating:
                elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
                minutes, seconds = divmod(elapsed_time, 60)
                draw_text(self.screen, f"Temps: {int(minutes):02}:{int(seconds):02}", self.ui_font, WHITE, 40, 120)
            # Draw last 5 moves
            draw_text(self.screen, "Derniers Coups:", self.ui_font, GOLD, 40, 160)
            for i, move in enumerate(self.move_history[-5:]):  # Show last 5 moves
                move_text = f"{move['source']} -> {move['destination']}"
                draw_text(self.screen, move_text, self.ui_font, WHITE, 40, 200 + i * 40)
            self.draw_credits()
        except Exception as e:
            print(f"Error in draw_game: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_game error: {str(e)}, n={self.n}, towers={self.towers}\n")
            raise

    def draw_win(self):
        try:
            self.draw_game(); self.draw_frosted_overlay()
            for p in self.particles: p.update(); p.draw(self.screen)
            self.particles = [p for p in self.particles if p.life > 0]
            message = "L'ordinateur a gagné !" if self.is_solver_used else ("Parfait !" if self.moves == self.min_moves else "Bravo !")
            draw_text(self.screen, message, self.title_font, GOLD, WIDTH / 2, HEIGHT / 2 - 100, centered=True)
            draw_text(self.screen, f"{self.player_name}, vous avez gagné !" if not self.is_solver_used else "Résolu par l'ordinateur !", self.menu_font, WHITE, WIDTH / 2, HEIGHT / 2, centered=True)
            draw_text(self.screen, "Appuyez pour voir les scores", self.ui_font, WHITE, WIDTH / 2, HEIGHT / 2 + 100, centered=True)
        except Exception as e:
            print(f"Error in draw_win: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_win error: {str(e)}, particles={len(self.particles)}\n")
            raise

    def draw_scoreboard(self):
        try:
            self.screen.blit(self.background_img, (0, 0)); self.draw_frosted_overlay()
            draw_text(self.screen, "Tableau des Scores", self.title_font, GOLD, WIDTH / 2, 70, centered=True)
            self.draw_buttons(self.ui_buttons)
            headers = ["Rang", "Nom", "Mouvements", "Temps"]
            for i, header in enumerate(headers): draw_text(self.screen, header, self.ui_font, GOLD, 150 + i * 250, 250)
            filtered_scores = sorted([s for s in self.scores if s.get('disks') == self.selected_score_difficulty], key=lambda s: (s.get('moves', 999), s.get('time', 999)))
            for i, score in enumerate(filtered_scores[:10]):
                y = 300 + i * 40; time_val = score.get('time', 0); minutes, seconds = divmod(time_val, 60)
                time_str = f"{int(minutes):02}:{seconds:05.2f}"
                data = [f"#{i+1}", score.get('name', '???'), str(score.get('moves', '-')), time_str]
                for j, item in enumerate(data): draw_text(self.screen, item, self.ui_font, WHITE, 150 + j * 250, y)
        except Exception as e:
            print(f"Error in draw_scoreboard: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_scoreboard error: {str(e)}, selected_score_difficulty={self.selected_score_difficulty}\n")
            raise

    def draw_how_to_play(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            self.draw_frosted_overlay()
            draw_text(self.screen, "Comment jouer", self.title_font, GOLD, WIDTH / 2, 100, centered=True)
            instructions = [
                "Le but est de déplacer tous les disques de la tour de gauche",
                "vers une autre tour (milieu ou droite), en respectant ces règles :",
                "1. Déplacez un disque à la fois en cliquant et en le glissant.",
                "2. Un disque plus grand ne peut pas être posé sur un disque plus petit.",
                "3. Utilisez la tour du milieu comme tour auxiliaire si nécessaire.",
                "4. Cliquez sur 'Solution' pour voir une résolution automatique.",
                "5. Essayez de minimiser le nombre de mouvements !"
            ]
            for i, line in enumerate(instructions):
                draw_text(self.screen, line, self.ui_font, WHITE, WIDTH / 2, 200 + i * 40, centered=True)
            self.draw_buttons(self.ui_buttons)
            self.screen.blit(self.logo_img, (WIDTH - self.logo_img.get_width() - 30, 30))
            self.draw_credits()
        except Exception as e:
            print(f"Error in draw_how_to_play: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_how_to_play error: {str(e)}\n")
            raise

    def draw_solver_explanation(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            self.draw_frosted_overlay()
            draw_text(self.screen, "Solveur?", self.title_font, GOLD, WIDTH / 2, 50, centered=True)
            explanation = [
                "Le problème des Tours de Hanoï est résolu par une approche récursive.",
                "Pour n disques, la solution suit ces étapes :",
                "1. Déplacez n-1 disques de la tour source à la tour auxiliaire.",
                "2. Déplacez le disque le plus grand de la tour source à la tour destination.",
                "3. Déplacez les n-1 disques de la tour auxiliaire à la tour destination.",
                "Cette récursivité se répète jusqu'à 1 disque.",
                "Le nombre minimum de mouvements est donné par la formule : 2ⁿ - 1.",
                "Exemple : Pour 3 disques, 2³ - 1 = 7 mouvements.",
                "Dérivation mathématique :",
                "  - Pour 1 disque : 1 mouvement.",
                "  - Pour n disques : 2 * (2^(n-1) - 1) + 1 = 2ⁿ - 1.",
                "Le solveur utilise cette logique pour générer la séquence optimale."
            ]
            for i, line in enumerate(explanation):
                draw_text(self.screen, line, self.ui_font, WHITE, WIDTH / 2, 150 + i * 40, centered=True)
            self.draw_buttons(self.ui_buttons)
            self.screen.blit(self.logo_img, (WIDTH - self.logo_img.get_width() - 30, 30))
            self.draw_credits()
        except Exception as e:
            print(f"Error in draw_solver_explanation: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_solver_explanation error: {str(e)}\n")
            raise

    def draw_history(self):
        try:
            self.screen.blit(self.background_img, (0, 0))
            self.draw_frosted_overlay()
            draw_text(self.screen, "Historique des Parties", self.title_font, GOLD, WIDTH / 2, 50, centered=True)
            y_start = 150
            for game in self.full_move_history:
                if game['game_id'] == self.game_id:
                    draw_text(self.screen, f"Partie: {game['player_name']} ({game['disks']} disques)", self.menu_font, WHITE, WIDTH / 2, y_start, centered=True)
                    y_start += 50
                    for i, move in enumerate(game['moves']):
                        move_text = f"Coup {i+1}: {move['source']} -> {move['destination']}"
                        draw_text(self.screen, move_text, self.ui_font, WHITE, WIDTH / 2, y_start + i * 40, centered=True)
                    y_start += len(game['moves']) * 40 + 50
            self.draw_buttons(self.ui_buttons)
            self.screen.blit(self.logo_img, (WIDTH - self.logo_img.get_width() - 30, 30))
            self.draw_credits()
        except Exception as e:
            print(f"Error in draw_history: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_history error: {str(e)}\n")
            raise

    # --- CORE LOGIC & ANIMATION ---
    def start_animation(self):
        try:
            self.animating = True
            self.is_solver_used = True  # Set flag when solver is used
            self.move_history = []  # Clear move history for solver
            self.moves = 0  # Reset move count

            # Use main game state instead of temporary state
            self.reset_disk_positions()
            original_buttons = self.ui_buttons.copy()
            solve_rect = original_buttons.get('solve', {}).get('rect', pygame.Rect(0,0,1,1))
            self.ui_buttons['stop'] = {'rect': solve_rect, 'text': 'Arrêter', 'color': STOP_RED}
            del self.ui_buttons['solve']

            solution = hanoi_solver(self.n, 0, 2, 1)

            for src, dest in solution:
                # Validate tower indices
                if not (0 <= src < len(self.towers) and 0 <= dest < len(self.towers)):
                    print(f"Invalid move: source={src}, destination={dest}")
                    with open("error.log", "a") as f:
                        f.write(f"Invalid move in animation: source={src}, destination={dest}, n={self.n}, towers={self.towers}\n")
                    self.sounds['invalid'].play()
                    self.ui_buttons = original_buttons
                    self.animating = False
                    return
                
                # Event handling to allow stopping the animation
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.ui_buttons['stop']['rect'].collidepoint(event.pos):
                            self.sounds['invalid'].play()
                            self.ui_buttons = original_buttons
                            self.animating = False
                            return

                if not self.towers[src]:
                    print(f"No disk to move from source tower {src}")
                    with open("error.log", "a") as f:
                        f.write(f"No disk to move in animation: source={src}, towers={self.towers}\n")
                    continue

                # Move disk in main game state
                disk_to_move = self.towers[src].pop()
                self.move_history.append({'source': src + 1, 'destination': dest + 1})
                self.moves += 1

                # Animate disk movement
                start_pos = disk_to_move['pos'].copy()
                mid_pos = pygame.Vector2((self.tower_rects[src].centerx + self.tower_rects[dest].centerx) / 2, 150)
                end_pos = pygame.Vector2(self.tower_rects[dest].centerx, self.tower_rects[dest].bottom - (len(self.towers[dest]) * disk_to_move['rect'].height))
                
                for i in range(int(0.4 * FPS)):
                    progress = ease_out_quad(i / int(0.4 * FPS))
                    if progress < 0.5:
                        disk_to_move['pos'] = start_pos.lerp(mid_pos, progress * 2)
                    else:
                        disk_to_move['pos'] = mid_pos.lerp(end_pos, (progress - 0.5) * 2)
                    
                    # Draw using draw_game to include move history
                    self.draw_game()
                    self.draw_single_disk(disk_to_move)  # Draw moving disk on top
                    self.draw_buttons(self.ui_buttons)
                    self.draw_credits()
                    pygame.display.flip()
                    self.clock.tick(FPS)
                
                # Place disk on destination tower
                self.towers[dest].append(disk_to_move)
                self.reset_disk_positions()

            # Animation finished
            self.ui_buttons = original_buttons
            self.animating = False
            self.check_win()
        except Exception as e:
            print(f"Animation error: {e}")
            with open("error.log", "a") as f:
                f.write(f"Animation error: {str(e)}, n={self.n}, towers={self.towers}\n")
            self.sounds['invalid'].play()
            self.ui_buttons = original_buttons
            self.animating = False

    def check_win(self):
        try:
            if self.towers and len(self.towers) >= 3 and (len(self.towers[1]) == self.n or len(self.towers[2]) == self.n):
                if self.game_state == 'win': return # Already in win state
                self.sounds['win'].play(); self.game_state = 'win'
                time_taken = (pygame.time.get_ticks() - self.start_time) / 1000
                if not self.is_solver_used:  # Only add score if solver wasn't used
                    self.scores.append({'name': self.player_name, 'disks': self.n, 'time': time_taken, 'moves': self.moves})
                    self.save_scoreboard()
                # Save move history
                self.full_move_history.append({
                    'game_id': self.game_id,
                    'player_name': self.player_name,
                    'disks': self.n,
                    'moves': self.move_history,
                    'time': time_taken
                })
                self.save_move_history()
                win_tower_idx = 1 if len(self.towers[1]) == self.n else 2
                if not DISK_PALETTE:
                    raise ValueError("DISK_PALETTE is empty")
                for _ in range(100):
                    self.particles.append(Particle(self.tower_rects[win_tower_idx].centerx, self.tower_rects[win_tower_idx].centery, random.choice(DISK_PALETTE)))
        except Exception as e:
            print(f"Error in check_win: {e}")
            with open("error.log", "a") as f:
                f.write(f"check_win error: {str(e)}, n={self.n}, towers={self.towers}\n")

    # --- HELPER FUNCTIONS ---
    def draw_buttons(self, buttons):
        try:
            mouse_pos = pygame.mouse.get_pos()
            for name, btn in buttons.items():
                # Safely check if the button name has a numeric suffix (e.g., score_3, disk_5)
                is_selected = False
                if 'score' in name:
                    name_parts = name.split('_')
                    if len(name_parts) > 1 and name_parts[1].isdigit():
                        is_selected = int(name_parts[1]) == self.selected_score_difficulty
                default_color = btn.get('color', PRIMARY_BLUE if is_selected else SECONDARY_BLUE)
                color = tuple(min(255, c * 1.2) for c in default_color) if btn['rect'].collidepoint(mouse_pos) else default_color
                pygame.draw.rect(self.screen, color, btn['rect'], border_radius=10)
                pygame.draw.rect(self.screen, WHITE, btn['rect'], 3, border_radius=10)
                draw_text(self.screen, btn['text'], self.ui_font, WHITE, btn['rect'].centerx, btn['rect'].centery, centered=True)
        except Exception as e:
            print(f"Error in draw_buttons: {e}, button_name={name}")
            with open("error.log", "a") as f:
                f.write(f"draw_buttons error: {str(e)}, button_name={name}, buttons={buttons}\n")
            raise

    def draw_single_disk(self, disk):
        try:
            color = disk.get('color', (128, 128, 128))
            disk['rect'].center = disk['pos']
            pygame.draw.rect(self.screen, color, disk['rect'], border_radius=5)
            border_color = [min(255, c * 0.8) for c in color]
            pygame.draw.rect(self.screen, border_color, disk['rect'], 3, border_radius=5)
        except Exception as e:
            print(f"Error in draw_single_disk: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_single_disk error: {str(e)}, disk={disk}\n")
            raise

    def draw_credits(self):
        try:
            draw_text(self.screen, "Designed by Redha_AGGOUN@La Plateforme_ 11.07.2025", self.credit_font, (255, 255, 255, 150), WIDTH / 2, HEIGHT - 20, centered=True)
        except Exception as e:
            print(f"Error in draw_credits: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_credits error: {str(e)}\n")
            raise

    def draw_frosted_overlay(self):
        try:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.blit(self.blurred_background, (0, 0))
            pygame.draw.rect(overlay, (0, 0, 0, 100), (0, 0, WIDTH, HEIGHT)); self.screen.blit(overlay, (0, 0))
        except Exception as e:
            print(f"Error in draw_frosted_overlay: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_frosted_overlay error: {str(e)}\n")
            raise

    def reset_disk_positions(self):
        try:
            if not self.towers or not self.tower_rects: return
            for i, tower in enumerate(self.towers):
                if i >= len(self.tower_rects):
                    print(f"Invalid tower index: {i}")
                    with open("error.log", "a") as f:
                        f.write(f"reset_disk_positions error: invalid tower index {i}, towers={self.towers}, tower_rects={self.tower_rects}\n")
                    return
                for j, disk in enumerate(tower):
                    disk['pos'] = pygame.Vector2(self.tower_rects[i].centerx, self.tower_rects[i].bottom - j * disk['rect'].height)
        except Exception as e:
            print(f"Error in reset_disk_positions: {e}")
            with open("error.log", "a") as f:
                f.write(f"reset_disk_positions error: {str(e)}, towers={self.towers}, tower_rects={self.tower_rects}\n")

    def draw_scenery(self):
        try:
            if not self.tower_rects: return
            base = pygame.Rect(WIDTH * 0.1, HEIGHT - 200, WIDTH * 0.8, 40)
            pygame.draw.rect(self.screen, (30, 30, 30), base, border_top_left_radius=10, border_top_right_radius=10)
            for t in self.tower_rects: pygame.draw.rect(self.screen, (80, 80, 80), t, border_radius=5)
        except Exception as e:
            print(f"Error in draw_scenery: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_scenery error: {str(e)}, tower_rects={self.tower_rects}\n")
            raise

    def draw_disks(self):
        try:
            disks_to_draw = [d for t in self.towers for d in t]
            for disk in disks_to_draw:
                if disk != self.dragging_disk: self.draw_single_disk(disk)
            if self.dragging_disk: self.draw_single_disk(self.dragging_disk)
        except Exception as e:
            print(f"Error in draw_disks: {e}")
            with open("error.log", "a") as f:
                f.write(f"draw_disks error: {str(e)}, towers={self.towers}, dragging_disk={self.dragging_disk}\n")
            raise

    def get_tower_at(self, pos):
        try:
            for i, t in enumerate(self.tower_rects):
                if t.inflate(100, 400).collidepoint(pos): return i
            return None
        except Exception as e:
            print(f"Error in get_tower_at: {e}")
            with open("error.log", "a") as f:
                f.write(f"get_tower_at error: {str(e)}, tower_rects={self.tower_rects}, pos={pos}\n")
            return None