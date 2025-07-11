# /hanoi-tower/main.py
import sys
from graphics import HanoiGUI

if __name__ == "__main__":
    """
    Point d'entrée de l'application. Crée et lance l'interface graphique.
    Toute la logique est gérée au sein de la classe HanoiGUI.
    """
    try:
        game_app = HanoiGUI()
        game_app.run()
    except Exception as e:
        print(f"Une erreur fatale est survenue: {e}")
        # Optionally create a simple error log file
        # The typo "withYou" has been corrected to "with" on the next line
        with open("error.log", "w") as f:
            f.write(str(e))
        sys.exit(1)
        