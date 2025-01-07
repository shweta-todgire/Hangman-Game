import pygame
import random
import time
import sqlite3 as sql

pygame.init()

HANGMAN_IMAGES = [pygame.image.load(f"assets/Hangman{i}.png") for i in range(7)]
CORRECT_SOUND = pygame.mixer.Sound("assets/correct.mp3")
WRONG_SOUND = pygame.mixer.Sound("assets/wrong.mp3")
WIN_SOUND = pygame.mixer.Sound("assets/win.mp3")
LOSE_SOUND = pygame.mixer.Sound("assets/loose.mp3")
HINT_SOUND = pygame.mixer.Sound("assets/hint.mp3")  

screen = pygame.display.set_mode((1500, 800), pygame.RESIZABLE)
pygame.display.set_caption("Hangman Game")

FPS = 60
clock = pygame.time.Clock()

class Database:
    def __init__(self):
        self.conn = sql.connect('hangman_game.db')
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            category TEXT NOT NULL
        )''')
        words = [
            ('elephant', 'Animal'),
            ('tiger', 'Animal'),
            ('giraffe', 'Animal'),
            ('kangaroo', 'Animal'),
            ('cat', 'Animal'),
            ('dog', 'Animal'),
            ('buffalo', 'Animal'),
            ('lion', 'Animal'),
            ('canada', 'Country'),
            ('india', 'Country'),
            ('germany', 'Country'),
            ('australia', 'Country'),
            ('brazil', 'Country'),
            ('america', 'Country'),
            ('sparrow', 'Bird'),
            ('parrot', 'Bird'),
            ('peacock', 'Bird'),
            ('owl', 'Bird'),
            ('pigeon', 'Bird'),
            ('crow', 'Bird'),
            ('eagle', 'Bird')
        ]
        self.cursor.executemany('INSERT INTO words (word, category) VALUES (?, ?)', words)
        self.conn.commit()

    def get_random_word(self, category):
        self.cursor.execute('SELECT word FROM words WHERE category = ? ORDER BY RANDOM() LIMIT 1', (category,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_categories(self):
        self.cursor.execute('SELECT DISTINCT category FROM words')
        categories = self.cursor.fetchall()
        return [category[0] for category in categories]

class Game:
    def __init__(self):
        self.database = Database()
        self.word = ""
        self.category = ""
        self.guesses = []
        self.attempts = 6
        self.score = 0
        self.running = True
        self.hint_revealed = False  

    def restart_game(self):
        self.category = random.choice(self.database.get_categories())
        self.word = self.database.get_random_word(self.category)
        self.guesses.clear()
        self.attempts = 6
        self.score = 0
        self.hint_revealed = False  
        self.main()

    def draw_screen(self):
        screen.fill("light blue")

        title = self.render_text("Hangman Game", 60, (0, 0, 139))
        category_surface = self.render_text(f"Category: {self.category}", 40, (128, 0, 128))

        display_text = " ".join([letter if letter in self.guesses else "_" for letter in self.word])
        word_surface = self.render_text(display_text, 30, (0, 0, 0))

        hangman_image = HANGMAN_IMAGES[6 - self.attempts]
        hangman_rect = hangman_image.get_rect(center=(750, 400))

        guesses_surface = self.render_text(f"Guesses: {', '.join(self.guesses)}", 30, (0, 128, 0))
        attempts_surface = self.render_text(f"Attempts left: {self.attempts}", 30, (255, 0, 0))

        hint_button_text = "Hint (only once)"
        hint_button = self.render_text(hint_button_text, 30, "black") 
        hint_button_rect = pygame.Rect(625, 675, 250, 50)  

        pygame.draw.rect(screen, "yellow", hint_button_rect)  
        pygame.draw.rect(screen, "orange", hint_button_rect, 3)  

        screen.blit(hint_button, hint_button.get_rect(center=hint_button_rect.center))

        screen.blit(title, title.get_rect(center=(750, 30)))
        screen.blit(category_surface, category_surface.get_rect(center=(750, 100)))
        screen.blit(word_surface, word_surface.get_rect(center=(750, 160)))
        screen.blit(hangman_image, hangman_rect)
        screen.blit(guesses_surface, guesses_surface.get_rect(center=(750, 600)))
        screen.blit(attempts_surface, attempts_surface.get_rect(center=(750, 650)))

        if self.hint_revealed:
            display_text = " ".join([letter if letter in self.guesses else "_" for letter in self.word])
            word_surface = self.render_text(display_text, 30, (0, 0, 0))

    def render_text(self, text, size, color):
        font = pygame.font.Font(pygame.font.match_font('Times New Roman'), size)
        surface = font.render(text, True, color)
        return surface

    def show_message(self, message, color):
        message_surface = self.render_text(message, 60, color)
        screen.blit(message_surface, message_surface.get_rect(center=(750, 300)))
        pygame.display.flip()
        time.sleep(2)

    def reveal_hint(self):
        hidden_letters = [letter for letter in self.word if letter not in self.guesses]
        if hidden_letters:
            hint_letter = random.choice(hidden_letters)
            self.guesses.append(hint_letter)
            self.hint_revealed = True
            HINT_SOUND.play()
            self.attempts -= 1  # Deduct one attempt for using a hint

    def main(self):
        self.category = random.choice(self.database.get_categories())
        self.word = self.database.get_random_word(self.category)
        self.guesses = []
        self.attempts = 6
        self.score = 0

        while self.running:
            clock.tick(FPS)
            self.draw_screen()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        hint_button_rect = pygame.Rect(625, 675, 150, 50) 
                        if hint_button_rect.collidepoint(event.pos) and not self.hint_revealed:
                            self.reveal_hint()  

                if event.type == pygame.KEYDOWN:
                    if event.unicode.isalpha():
                        guess = event.unicode.lower()
                        if guess not in self.guesses:
                            self.guesses.append(guess)
                            if guess not in self.word:
                                self.attempts -= 1
                                WRONG_SOUND.play()
                            else:
                                CORRECT_SOUND.play()

            self.draw_screen()

            if all(letter in self.guesses for letter in self.word):
                WIN_SOUND.play()
                self.score = 100 - 10 * (6 - self.attempts)
                self.show_message(f"You Win! Score: {self.score}/100", (0, 128, 0))
                self.restart_game()  
            if self.attempts == 0:
                LOSE_SOUND.play()
                self.show_message(f"You Lose! Word: {self.word}", (255, 0, 0))
                self.restart_game()  

            pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.main()
    pygame.quit()
