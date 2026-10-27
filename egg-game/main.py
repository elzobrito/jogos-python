#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ponto de entrada de Egg Game: De Volta ao Ninho (`python3 main.py [--demo]`)."""

from __future__ import annotations

import argparse
import sys

from egg_game.app import EggGameApp
from egg_game.core.constants import DEFAULT_SEED


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Egg Game: De Volta ao Ninho (MVP Aventura — Pygame-CE)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa piloto automático e salva prints em prints/ (titulo, modo, jogo, pausa, gameover, vitoria).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed determinística para o gerador de cestas.",
    )
    args = parser.parse_args()

    app = EggGameApp(demo_mode=args.demo, seed=args.seed)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
