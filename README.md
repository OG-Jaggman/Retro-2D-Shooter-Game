# Retro 2D Shooter

A simple retro-style 2D shooter game built with Python and Pygame.

## Requirements

- Python 3.x
- Pygame

## Installation

1. Clone or download the repository.
2. Create a virtual environment in the project folder:
   ```
   python -m venv .venv
   ```
3. Install dependencies:
   - Double-click `install_requirements.bat` to install the required packages into the virtual environment, or run:
     ```
     .venv\Scripts\activate
     pip install -r requirements.txt
     ```

## Running the Game

Double-click `run_game.bat` to start the game, or activate the virtual environment and run `python main.py` from the command line.

Note: The batch files handle activating the virtual environment automatically.

## Features

- Main menu with Start Game, Directions, Credits, and Toggle Fullscreen
- Player ship with movement and shooting
- Enemy spawning and collision detection
- Score system with persistent high score tracking
- Pause functionality with resume, give up, and main menu options
- Game over screen with retry and main menu options

## Controls

- Movement: Arrow keys or WASD (A=left, D=right)
- Shoot: Space or Left mouse click
- ESC: Pause/Unpause
- Mouse: Click buttons in menus