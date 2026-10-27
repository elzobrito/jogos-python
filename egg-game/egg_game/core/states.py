# -*- coding: utf-8 -*-
"""Enumerações das máquinas de estados do aplicativo e do ovo protagonista."""

from __future__ import annotations

from enum import Enum


class AppState(str, Enum):
    """Estados globais do aplicativo conforme SPEC §1, §10 e PRD §12."""

    BOOT = "BOOT"
    MAIN_MENU = "MAIN_MENU"
    MODE_SELECT = "MODE_SELECT"
    INTRO = "INTRO"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    DEATH_ANIMATION = "DEATH_ANIMATION"
    GAME_OVER = "GAME_OVER"
    VICTORY = "VICTORY"
    SETTINGS = "SETTINGS"


class EggState(str, Enum):
    """Estados físicos e de animação do ovo conforme PRD §7.1 e SPEC §0.2."""

    IDLE = "IDLE"
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"
    LANDING = "LANDING"
    DYING = "DYING"
    DEAD = "DEAD"
    CELEBRATING = "CELEBRATING"
