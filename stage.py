#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

class Stage:
    """Enum representing the game process state"""
    
    STOP = -1
    MAIN_MENU = 0
    NAMEINPUT = 1
    WAITING_OPPONENT = 2
    COUNTDOWN = 3
    IN_GAME = 4
    GAME_TO_BREAKDOWN = 5
    BREAKDOWN_BAR = 6
    BREAKDOWN_BONUSES = 7
    TUTORIAL = 8
    CREDITS = 9