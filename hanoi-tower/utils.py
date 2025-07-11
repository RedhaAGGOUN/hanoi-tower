import pygame
import math
import random

def draw_text(surface, text, font, color, x, y, centered=False):
    try:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if centered:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_surface, text_rect)
    except Exception as e:
        print(f"Error in draw_text: {e}")
        with open("error.log", "a") as f:
            f.write(f"draw_text error: {str(e)}, text={text}\n")

def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

class Particle:
    def __init__(self, x, y, color):
        try:
            self.x = x
            self.y = y
            self.vx = (2 * random.random() - 1) * 5
            self.vy = (2 * random.random() - 1) * 5
            self.color = color
            self.life = 100
            self.size = 5
        except Exception as e:
            print(f"Error in Particle.__init__: {e}")
            with open("error.log", "a") as f:
                f.write(f"Particle.__init__ error: {str(e)}\n")

    def update(self):
        try:
            self.x += self.vx
            self.y += self.vy
            self.life -= 1
            self.size = max(1, self.size - 0.05)
        except Exception as e:
            print(f"Error in Particle.update: {e}")
            with open("error.log", "a") as f:
                f.write(f"Particle.update error: {str(e)}\n")

    def draw(self, surface):
        try:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))
        except Exception as e:
            print(f"Error in Particle.draw: {e}")
            with open("error.log", "a") as f:
                f.write(f"Particle.draw error: {str(e)}\n")

class TextInputBox:
    def __init__(self, x, y, w, h, font, initial_text=""):
        try:
            self.rect = pygame.Rect(x, y, w, h)
            self.text = initial_text
            self.font = font
            self.active = False
            self.cursor_visible = True
            self.cursor_timer = 0
        except Exception as e:
            print(f"Error in TextInputBox.__init__: {e}")
            with open("error.log", "a") as f:
                f.write(f"TextInputBox.__init__ error: {str(e)}, initial_text={initial_text}\n")
            raise

    def handle_event(self, event):
        try:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)
            if self.active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return 'enter'
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif len(self.text) < 20:  # Limit input length
                    self.text += event.unicode
            return None
        except Exception as e:
            print(f"Error in TextInputBox.handle_event: {e}")
            with open("error.log", "a") as f:
                f.write(f"TextInputBox.handle_event error: {str(e)}, text={self.text}\n")
            return None

    def update(self):
        try:
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
        except Exception as e:
            print(f"Error in TextInputBox.update: {e}")
            with open("error.log", "a") as f:
                f.write(f"TextInputBox.update error: {str(e)}\n")

    def draw(self, surface):
        try:
            pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=10)
            pygame.draw.rect(surface, (0, 0, 0) if self.active else (100, 100, 100), self.rect, 3, border_radius=10)
            text_surface = self.font.render(self.text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery))  # Center text vertically
            surface.blit(text_surface, text_rect)
            if self.active and self.cursor_visible:
                text_width = self.font.render(self.text, True, (0, 0, 0)).get_width()
                cursor_x = self.rect.x + 10 + text_width
                cursor_y = self.rect.centery - text_surface.get_height() // 2
                pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y + 5), (cursor_x, cursor_y + text_surface.get_height() - 5))
        except Exception as e:
            print(f"Error in TextInputBox.draw: {e}")
            with open("error.log", "a") as f:
                f.write(f"TextInputBox.draw error: {str(e)}, text={self.text}\n")