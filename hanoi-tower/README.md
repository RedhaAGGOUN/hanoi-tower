# Tower of Hanoi - Souvenir de Voyage (Édition Améliorée)

Ce projet est une implémentation premium et visuellement riche du puzzle des Tours de Hanoï, développé pour La Plateforme. Il transforme l'exercice algorithmique en une application interactive et esthétiquement plaisante.

## Problématique

L'objectif initial était de créer un solveur récursif pour les Tours de Hanoï avec une simple interface. Cette version améliorée répond à un défi supérieur : **créer une expérience utilisateur exceptionnelle** pour le même problème.

Les exigences sont :
1.  Une logique de résolution récursive qui garantit le nombre minimal de coups.
2.  Une interface graphique de haute qualité, moderne et intuitive.
3.  Des animations fluides pour la résolution automatique.
4.  Une interaction utilisateur via glisser-déposer (Drag & Drop).
5.  Un retour visuel et auditif clair pour guider le joueur.

## Solution Proposée : L'Expérience Pygame

Pour atteindre un niveau de qualité graphique et d'interactivité élevé, la bibliothèque `tkinter` a été remplacée par **`Pygame`**, un standard pour le développement de jeux 2D en Python.

### Architecture
- **`solve.py`**: Le cœur algorithmique. Contient la fonction récursive `hanoi_solver`, inchangée et parfaitement fonctionnelle.
- **`graphics.py`**: Le chef-d'œuvre visuel. Entièrement réécrit avec `Pygame`, ce module gère :
  - La boucle de jeu principale.
  - Le rendu de tous les éléments graphiques (disques, tours, arrière-plan).
  - La gestion des événements utilisateur (clics, glisser-déposer).
  - L'animation fluide et cinématique de la solution automatique.
  - Le chargement et la lecture des sons pour une expérience immersive.
- **`main.py`**: Le lanceur. Utilise `argparse` pour une gestion propre des arguments en ligne de commande. Il lance par défaut l'interface graphique mais peut aussi exécuter le solveur en mode terminal.
- **`assets/`**: Un dossier dédié aux ressources (images, polices, sons) pour séparer le code de la data.

### Fonctionnalités Clés
- **Esthétique Soignée**: Un magnifique arrière-plan inspiré du voyage, des disques colorés, des polices personnalisées et une interface épurée.
- **Interaction Intuitive**: Jouez en attrapant un disque avec la souris et en le déposant sur une autre tour.
- **Feedback Immédiat**:
  - **Visuel**: Les tours de destination s'illuminent en vert (valide) ou en rouge (invalide) lorsque vous survolez avec un disque.
  - **Auditif**: Des sons distincts pour prendre un disque, le poser, tenter un coup invalide et gagner la partie.
- **Animation "Cinématique"**: La résolution automatique n'est plus une succession d'états, mais une animation fluide où chaque disque se déplace de manière réaliste sur l'écran.

## Installation et Lancement

**1. Dépendances**

Ce projet nécessite la bibliothèque `Pygame`. Installez-la via pip :
```bash
pip install pygame
```

**2. Lancement**

Clonez ce repository. Assurez-vous que le dossier `assets` est présent avec les fichiers nécessaires.

**Pour lancer l'interface graphique (recommandé)** :
```bash
# Avec 5 disques par défaut
python main.py

# Pour spécifier un nombre de disques (ex: 7)
python main.py "7,3"
```

**Pour lancer la résolution en mode terminal** :
```bash
python main.py "8,3" --mode terminal
```

## Conclusion

Cette version du projet "Tower of Hanoi" démontre comment un problème algorithmique classique peut être transcendé en une expérience logicielle complète et agréable. En choisissant les bons outils (`Pygame`) et en se concentrant sur les détails de l'expérience utilisateur (animations, sons, feedback), le projet passe d'une "preuve de concept" à un "produit" poli et engageant. Les compétences mises en œuvre incluent non seulement l'algorithmique et la récursivité, mais aussi la conception de jeux, la gestion d'états complexes et le développement d'interfaces homme-machine efficaces.