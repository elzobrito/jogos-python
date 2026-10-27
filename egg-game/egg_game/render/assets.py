# -*- coding: utf-8 -*-
"""
Gerenciador de assets visuais do Egg Game:
- Sprites do ovo, cestas, ninho e itens em `assets/sprites/` (SPEC §2)
- Camadas de paralaxe v3 em `assets/backgrounds/` (SPEC §11)
- Peças da árvore modular v3 em `assets/tree/`, `galhos/` e `folhas/` (SPEC §11)
- Telas e placas de madeira HUD v2 em `assets/bg/` (SPEC §10)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

DIRETORIO_ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
DIRETORIO_SPRITES_PADRAO = DIRETORIO_ASSETS / "sprites"
DIRETORIO_BG_V2 = DIRETORIO_ASSETS / "bg"
DIRETORIO_BACKGROUNDS_V3 = DIRETORIO_ASSETS / "backgrounds"
DIRETORIO_TREE_V3 = DIRETORIO_ASSETS / "tree"


class AssetManager:
    """Carrega e faz cache dos sprites RGBA, fundos de paralaxe v3, árvore modular v3 e telas/HUD v2."""

    def __init__(self, sprites_dir: Optional[Path] = None) -> None:
        self.sprites_dir = sprites_dir or DIRETORIO_SPRITES_PADRAO
        self._raw_cache: Dict[str, pygame.Surface] = {}
        self._scaled_cache: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self._path_cache: Dict[Path, pygame.Surface] = {}

        self.egg_idle: List[pygame.Surface] = []
        self.egg_jump: List[pygame.Surface] = []
        self.egg_fall: List[pygame.Surface] = []
        self.egg_death: List[pygame.Surface] = []
        self.nest_glow: List[pygame.Surface] = []

        # Camadas de paralaxe v3 (`assets/backgrounds/`)
        self.bg_ceu: Optional[pygame.Surface] = None
        self.bg_nuvens: Optional[pygame.Surface] = None
        self.bg_montanhas: Optional[pygame.Surface] = None
        self.bg_vilarejo: Optional[pygame.Surface] = None

        # Árvore modular v3 / Round 3 (`assets/tree/`)
        self.trunk_repeat: Optional[pygame.Surface] = None
        self.tree_parts: List[pygame.Surface] = []
        self.tronco_base: Optional[pygame.Surface] = None
        self.tronco_a: Optional[pygame.Surface] = None
        self.tronco_b: Optional[pygame.Surface] = None
        self.tronco_c: Optional[pygame.Surface] = None
        self.tronco_topo: Optional[pygame.Surface] = None
        self.tree_galhos: Dict[str, pygame.Surface] = {}
        self.tree_folhas: List[pygame.Surface] = []

        # HUD e telas de estado v2 (`assets/bg/`)
        self.hud_placa_altura: Optional[pygame.Surface] = None
        self.hud_placa_recorde: Optional[pygame.Surface] = None
        self.hud_btn_pausa: Optional[pygame.Surface] = None
        self.screens_v2: Dict[str, pygame.Surface] = {}
        self.galho_suporte_esq: Optional[pygame.Surface] = None
        self.galho_suporte_dir: Optional[pygame.Surface] = None

    def _load_surface_path(self, path: Path, use_alpha: bool = True) -> pygame.Surface:
        """Carrega um arquivo PNG arbitrário com cache e conversão de formato se houver display."""
        resolved = path.resolve()
        if resolved not in self._path_cache:
            if not resolved.exists():
                raise FileNotFoundError(f"Asset obrigatório ausente: {resolved}")
            surf = pygame.image.load(str(resolved))
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha() if use_alpha else surf.convert()
            self._path_cache[resolved] = surf
        return self._path_cache[resolved]

    def load_all(self) -> None:
        """Carrega todos os arquivos PNG obrigatórios definidos na SPEC §2, §10 e §11."""
        # 1. Sprites do ovo, cestas e ninho (`assets/sprites/`)
        self.egg_idle = [
            self.get_scaled(f"egg_idle_0{i}.png", (86, 102))
            for i in range(5)
        ]
        self.egg_jump = [
            self.get_scaled(f"egg_jump_0{i}.png", (86, 104))
            for i in range(6)
        ]
        self.egg_fall = [
            self.get_scaled(f"egg_fall_0{i}.png", (86, 106))
            for i in range(4)
        ]
        self.egg_death = [
            self.get_scaled(f"egg_death_0{i}.png", (118, 118))
            for i in range(4)
        ]
        self.nest_glow = [
            self.get_scaled(f"nest_glow_0{i}.png", (230, 150))
            for i in range(3)
        ]

        for nome in (
            "basket_static_01.png",
            "basket_leaves_01.png",
            "basket_leaves_02.png",
            "basket_fragile_01.png",
            "basket_cloud_01.png",
            "basket_ice_01.png",
            "basket_ice_02.png",
            "basket_fake_01.png",
            "nest_final.png",
            "item_shield.png",
            "item_feather.png",
            "item_star.png",
            "item_heart.png",
            "item_clock.png",
        ):
            self.get_raw(nome)

        # 2. Camadas de paralaxe v3 (`assets/backgrounds/`)
        self.bg_ceu = self._load_surface_path(DIRETORIO_BACKGROUNDS_V3 / "ceu.png", use_alpha=True)
        self.bg_nuvens = self._load_surface_path(DIRETORIO_BACKGROUNDS_V3 / "nuvens.png", use_alpha=True)
        self.bg_montanhas = self._load_surface_path(DIRETORIO_BACKGROUNDS_V3 / "montanhas.png", use_alpha=True)
        self.bg_vilarejo = self._load_surface_path(DIRETORIO_BACKGROUNDS_V3 / "vilarejo.png", use_alpha=True)

        # 3. Árvore modular v3 / Round 3 (`assets/tree/`)
        self.trunk_repeat = self._load_surface_path(DIRETORIO_TREE_V3 / "trunk_repeat.png", use_alpha=True)
        self.tree_parts = [
            self._load_surface_path(DIRETORIO_TREE_V3 / f"trunk_{c}.png", use_alpha=True)
            for c in "ABCDEFG"
        ]
        self.tronco_base = self._load_surface_path(DIRETORIO_TREE_V3 / "tronco_base.png", use_alpha=True)
        self.tronco_a = self._load_surface_path(DIRETORIO_TREE_V3 / "tronco_a.png", use_alpha=True)
        self.tronco_b = self._load_surface_path(DIRETORIO_TREE_V3 / "tronco_b.png", use_alpha=True)
        self.tronco_c = self._load_surface_path(DIRETORIO_TREE_V3 / "tronco_c.png", use_alpha=True)
        self.tronco_topo = self._load_surface_path(DIRETORIO_TREE_V3 / "tronco_topo.png", use_alpha=True)

        for gname in ("galho_esq_01", "galho_esq_02", "galho_dir_01", "galho_dir_02"):
            self.tree_galhos[gname] = self._load_surface_path(
                DIRETORIO_TREE_V3 / "galhos" / f"{gname}.png", use_alpha=True
            )

        self.tree_folhas = [
            self._load_surface_path(DIRETORIO_TREE_V3 / "folhas" / f"folhas_0{i}.png", use_alpha=True)
            for i in range(1, 5)
        ]

        # 4. Placas de madeira da HUD e telas v2 (`assets/bg/`)
        self.hud_placa_altura = self._load_surface_path(DIRETORIO_BG_V2 / "hud_placa_altura.png", use_alpha=True)
        self.hud_placa_recorde = self._load_surface_path(DIRETORIO_BG_V2 / "hud_placa_recorde.png", use_alpha=True)
        self.hud_btn_pausa = self._load_surface_path(DIRETORIO_BG_V2 / "hud_btn_pausa.png", use_alpha=True)

        for screen_key, fname, has_alpha in (
            ("menu", "tela_menu_base.png", False),
            ("modo", "tela_modo_base.png", False),
            ("comojogar", "tela_comojogar_base.png", False),
            ("pausa_base", "tela_pausa_base.png", False),
            ("pausa_painel", "tela_pausa_painel.png", True),
            ("gameover", "tela_gameover_base.png", False),
            ("vitoria", "tela_vitoria_base.png", False),
            ("opcoes", "tela_opcoes_base.png", False),
        ):
            self.screens_v2[screen_key] = self._load_surface_path(DIRETORIO_BG_V2 / fname, use_alpha=has_alpha)

        self.galho_suporte_esq = self._load_surface_path(DIRETORIO_BG_V2 / "galho_esq.png", use_alpha=True)
        self.galho_suporte_dir = self._load_surface_path(DIRETORIO_BG_V2 / "galho_dir.png", use_alpha=True)

    def get_raw(self, filename: str) -> pygame.Surface:
        """Carrega um PNG RGBA de `assets/sprites/` (com convert_alpha se houver display)."""
        if filename not in self._raw_cache:
            caminho = self.sprites_dir / filename
            if not caminho.exists():
                raise FileNotFoundError(
                    f"Sprite obrigatório ausente: {caminho}. Execute `python3 tools/recortar_sprites.py`."
                )
            superficie = pygame.image.load(str(caminho))
            if pygame.display.get_surface() is not None:
                superficie = superficie.convert_alpha()
            self._raw_cache[filename] = superficie
        return self._raw_cache[filename]

    def get_scaled(self, filename: str, target_box: Tuple[int, int]) -> pygame.Surface:
        """
        Redimensiona preservando proporção para caber dentro de `target_box = (max_w, max_h)`.
        """
        chave = (filename, target_box[0], target_box[1])
        if chave not in self._scaled_cache:
            bruto = self.get_raw(filename)
            bw, bh = bruto.get_size()
            escala = min(target_box[0] / max(1, bw), target_box[1] / max(1, bh))
            nw = max(1, int(round(bw * escala)))
            nh = max(1, int(round(bh * escala)))
            self._scaled_cache[chave] = pygame.transform.smoothscale(bruto, (nw, nh))
        return self._scaled_cache[chave]

    def get_basket_surface(self, variant: str, width: float) -> pygame.Surface:
        """Retorna o sprite da cesta ou ninho escalado para a largura física da plataforma."""
        arquivo = variant if variant.endswith(".png") else f"{variant}.png"
        if "nest" in arquivo:
            alvo_w = int(round(width * 1.18))
            alvo_h = int(round(alvo_w * 0.62))
        else:
            # Cestas têm pequena folga visual nas bordas da palha em relação à largura útil
            alvo_w = int(round(width * 1.16))
            alvo_h = int(round(alvo_w * 0.62))
        return self.get_scaled(arquivo, (alvo_w, alvo_h))
