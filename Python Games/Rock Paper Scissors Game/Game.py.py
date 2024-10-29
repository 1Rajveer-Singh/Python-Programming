import pyttsx3
import random
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk
import os

# Initialize the text-to-speech engine
engine = pyttsx3.init('sapi5')
engine.setProperty('voice', engine.getProperty('voices')[0].id)
engine.setProperty('rate', 180)

def speak(audio):
    """Speak the provided audio text."""
    engine.say(audio)
    engine.runAndWait()

def wishme():
    """Greet the user based on the current time."""
    hour = datetime.now().hour
    if hour < 12:
        speak("Good Morning")
    elif hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

class RockPaperScissorsGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock-Paper-Scissors Game")
        self.root.geometry("400x700")
        self.root.configure(bg="#1F1B24")

        self.choices = ["Rock", "Paper", "Scissors"]
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0

        self.create_widgets()

    def create_widgets(self):
        """Create the game widgets."""
        # Title Label
        self.title_label = tk.Label(self.root, text="Rock-Paper-Scissors Game", 
                                     font=("Arial", 20, "bold"), bg="#FF6F61", fg="white")
        self.title_label.pack(pady=10, fill="x")

        # Image Frame for icons
        self.choice_frame = tk.Frame(self.root, bg="#393E46", bd=5, relief="groove")
        self.choice_frame.pack(pady=20, padx=20, fill="x")

        self.choice_label = tk.Label(self.choice_frame, text="Choose one:", 
                                      font=("Arial", 16), bg="#393E46", fg="white")
        self.choice_label.pack(pady=10)

        # Load images for choices
        self.images = self.load_images()

        # Create buttons for choices with spacing
        self.choice_var = tk.StringVar(value="Rock")
        for choice in self.choices:
            btn = tk.Radiobutton(
                self.choice_frame, 
                image=self.images[choice], 
                text=choice, 
                variable=self.choice_var, 
                value=choice, 
                font=("Arial", 14), 
                bg="#393E46", 
                indicator=0, 
                bd=1, 
                relief="solid", 
                selectcolor="#FF6F61", 
                command=self.update_choice
            )
            btn.pack(side="left", padx=(10, 20), pady=10)  # Added padding for spacing

        # Play Button with countdown
        self.play_button = tk.Button(self.root, text="Play", command=self.start_countdown, 
                                      font=("Arial", 16, "bold"), bg="#00ADB5", fg="white", 
                                      width=15, bd=3, relief="raised")
        self.play_button.pack(pady=20)

        # Result Box for showing round results
        self.result_frame = tk.Frame(self.root, bg="#393E46", bd=5, relief="groove")
        self.result_frame.pack(pady=10, padx=20, fill="x")

        self.result_label = tk.Label(self.result_frame, text="Round Result:", 
                                      font=("Arial", 16), bg="#393E46", fg="white")
        self.result_label.pack()

        self.result_text = tk.Label(self.result_frame, text="", 
                                     font=("Arial", 14), bg="#393E46", fg="white", 
                                     wraplength=300, justify="center")
        self.result_text.pack()

        # Score Frame
        self.score_frame = tk.Frame(self.root, bg="#393E46", bd=5, relief="groove")
        self.score_frame.pack(pady=20, padx=20, fill="x")

        self.score_label = tk.Label(self.score_frame, text="Scores", 
                                     font=("Arial", 16, "bold"), bg="#393E46", fg="white")
        self.score_label.pack(pady=5)

        # Player and Computer Scores
        self.player_score_label = tk.Label(self.score_frame, text="Player: 0", 
                                            font=("Arial", 14), bg="#393E46", fg="white")
        self.player_score_label.pack()

        self.computer_score_label = tk.Label(self.score_frame, text="Computer: 0", 
                                              font=("Arial", 14), bg="#393E46", fg="white")
        self.computer_score_label.pack()

        # Draws
        self.draws_label = tk.Label(self.score_frame, text="Draws: 0", 
                                     font=("Arial", 14), bg="#393E46", fg="white")
        self.draws_label.pack()

        # Reset and Exit Buttons
        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset_game, 
                                       font=("Arial", 16, "bold"), bg="#FF5722", fg="white", 
                                       width=15, bd=3, relief="raised")
        self.reset_button.pack(pady=10)

        self.exit_button = tk.Button(self.root, text="Exit Game", command=self.exit_game, 
                                     font=("Arial", 16, "bold"), bg="#FF5722", fg="white", 
                                     width=15, bd=3, relief="raised")
        self.exit_button.pack(pady=10)

    def load_images(self):
        """Load images for the game choices."""
        images = {}
        for choice in self.choices:
            img_path = f"{choice.lower()}.png"
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((100, 100), Image.LANCZOS)
                images[choice] = ImageTk.PhotoImage(img)
            else:
                messagebox.showerror("Image Error", f"Image file {img_path} not found.")
                self.root.quit()
        return images

    def update_choice(self):
        """Placeholder for future functionality when a choice is selected."""
        pass

    def start_countdown(self):
        """Start a countdown before playing a round."""
        self.result_text.config(text="3...")
        self.root.after(1000, lambda: self.result_text.config(text="2..."))
        self.root.after(2000, lambda: self.result_text.config(text="1..."))
        self.root.after(3000, self.play_round)

    def play_round(self):
        """Play a round of the game and determine the result."""
        player_choice = self.choice_var.get()
        computer_choice = random.choice(self.choices)

        # Determine the result
        if player_choice == computer_choice:
            self.draws += 1
            result_text = "It's a draw!"
        elif (player_choice == "Rock" and computer_choice == "Scissors") or \
             (player_choice == "Paper" and computer_choice == "Rock") or \
             (player_choice == "Scissors" and computer_choice == "Paper"):
            self.player_score += 1
            result_text = "You win this round!"
        else:
            self.computer_score += 1
            result_text = "Computer wins this round!"

        # Update the GUI
        self.update_scoreboard(result_text, player_choice, computer_choice)

        # Announce the result
        self.root.after(500, lambda: self.announce_round_result(result_text, player_choice, computer_choice))

    def update_scoreboard(self, result_text, player_choice, computer_choice):
        """Update the scoreboard and result display."""
        self.result_text.config(text=f"Player: {player_choice} | Computer: {computer_choice}\n{result_text}")
        self.player_score_label.config(text=f"Player: {self.player_score}")
        self.computer_score_label.config(text=f"Computer: {self.computer_score}")
        self.draws_label.config(text=f"Draws: {self.draws}")

    def announce_round_result(self, result_text, player_choice, computer_choice):
        """Announce the round result using text-to-speech."""
        speak(f"Player chose {player_choice}. Computer chose {computer_choice}. {result_text}")
        speak(f"Current score: Player: {self.player_score}, Computer: {self.computer_score}, Draws: {self.draws}")

    def exit_game(self):
        """Exit the game and announce final results."""
        final_message = f"Final Results. Player: {self.player_score}. Computer: {self.computer_score}. Draws: {self.draws}."
        if self.player_score > self.computer_score:
            final_message += " Player is the Winner!"
        elif self.computer_score > self.player_score:
            final_message += " Computer is the Winner!"
        else:
            final_message += " It's a draw!"
        
        speak(final_message)
        messagebox.showinfo("Game Over", final_message)
        self.root.quit()

    def reset_game(self):
        """Reset the game to its initial state."""
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0
        self.result_text.config(text="")
        self.player_score_label.config(text="Player: 0")
        self.computer_score_label.config(text="Computer: 0")
        self.draws_label.config(text="Draws: 0")
        speak("Game reset. Let's play again!")

if __name__ == "__main__":
    root = tk.Tk()
    game = RockPaperScissorsGame(root)
    root.after(1000, wishme)
    root.mainloop()
