# -*- coding: utf-8 -*-
"""Configuração do pytest para garantir que a raiz do projeto esteja no sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
