#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de recorte e limpeza dos sprites de `ref/ref_1.jpg`.

Recorta a grade 8x5 (células de 180x170 px em uma imagem 1440x850),
remove os rótulos inferiores/superiores, aplica flood-fill + color-key sobre
o fundo bege RGB(233, 225, 212), limpa o halo nas bordas, faz o trim da
caixa delimitadora opaca e salva os PNGs RGBA em `assets/sprites/` com os
nomes padronizados da SPEC.md, além de gerar `tools/contact_sheet.png`.
"""

from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_REF1 = DIRETORIO_RAIZ / "ref" / "ref_1.jpg"
PASTA_SAIDA = DIRETORIO_RAIZ / "assets" / "sprites"
CAMINHO_CONTACT_SHEET = DIRETORIO_RAIZ / "tools" / "contact_sheet.png"

COR_FUNDO_BEGE = (233, 225, 212)
COLUNAS = 8
LINHAS = 5
LARGURA_CELULA = 180
ALTURA_CELULA = 170

# Mapeamento (linha, coluna) -> (nome_original_na_folha, nome_arquivo_spec)
MAPA_CELULAS: List[Tuple[int, int, str, str]] = [
    # Linha 0
    (0, 0, "idle_04", "egg_idle_03.png"),
    (0, 1, "idle_01", "egg_idle_00.png"),
    (0, 2, "idle_05", "egg_idle_04.png"),
    (0, 3, "idle_03", "egg_idle_02.png"),
    (0, 4, "idle_02", "egg_idle_01.png"),
    (0, 5, "jump_06", "egg_jump_05.png"),
    (0, 6, "jump_05", "egg_jump_04.png"),
    (0, 7, "jump_03", "egg_jump_02.png"),
    # Linha 1
    (1, 0, "jump_01", "egg_jump_00.png"),
    (1, 1, "jump_04", "egg_jump_03.png"),
    (1, 2, "jump_02", "egg_jump_01.png"),
    (1, 3, "fall_03", "egg_fall_02.png"),
    (1, 4, "fall_01", "egg_fall_00.png"),
    (1, 5, "fall_04", "egg_fall_03.png"),
    (1, 6, "fall_02", "egg_fall_01.png"),
    (1, 7, "death_03", "egg_death_02.png"),
    # Linha 2
    (2, 0, "death_01", "egg_death_00.png"),
    (2, 1, "death_04", "egg_death_03.png"),
    (2, 2, "death_02", "egg_death_01.png"),
    (2, 3, "pequena_02", "basket_static_01.png"),
    (2, 4, "fragil_02", "basket_fragile_01.png"),
    (2, 5, "folhas_01", "basket_leaves_01.png"),
    (2, 6, "nuvem_02", "basket_cloud_01.png"),
    (2, 7, "folhas_02", "basket_leaves_02.png"),
    # Linha 3
    (3, 0, "gelo_02", "basket_ice_02.png"),
    (3, 1, "falsa_02", "basket_fake_01.png"),
    (3, 2, "gelo_01", "basket_ice_01.png"),
    (3, 3, "ninho_final", "nest_final.png"),
    (3, 4, "ninho_brilho_01", "nest_glow_00.png"),
    (3, 5, "ninho_brilho_03", "nest_glow_02.png"),
    (3, 6, "ninho_brilho_02", "nest_glow_01.png"),
    (3, 7, "escudo", "item_shield.png"),
    # Linha 4
    (4, 0, "pena", "item_feather.png"),
    (4, 1, "estrela", "item_star.png"),
    (4, 2, "coracao", "item_heart.png"),
    (4, 3, "relogio", "item_clock.png"),
]

# Recortes verticais específicos (topo_min_y, base_max_y) para excluir rótulos residuais
LIMITES_Y_ESPECIFICOS: Dict[str, Tuple[int, int]] = {
    "ninho_final": (33, 136),
    "ninho_brilho_01": (12, 136),
    "ninho_brilho_02": (12, 136),
    "ninho_brilho_03": (4, 136),
    "escudo": (4, 113),
    "relogio": (4, 118),
}


def distancia_cor(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calcula a distância euclidiana entre duas cores RGB."""
    return math.sqrt(
        (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2
    )


def remover_fundo_e_halo(
    celula_rgb: Image.Image,
    tolerancia_flood: float = 11.5,
    tolerancia_halo: float = 28.0,
) -> Image.Image:
    """
    Remove o fundo bege RGB(233, 225, 212) combinando:
    1. Flood-fill estrito a partir das bordas externas (preservando o interior creme do ovo).
    2. Suavização e descontaminação de cor (de-halo) apenas na borda externa de 1px.
    """
    largura, altura = celula_rgb.size
    rgba = celula_rgb.convert("RGBA")
    pixels = rgba.load()

    fundo_visitado = [[False] * largura for _ in range(altura)]
    fila: deque[Tuple[int, int]] = deque()

    # Sementes em todo o perímetro da imagem recortada
    for x in range(largura):
        fila.append((x, 0))
        fila.append((x, altura - 1))
    for y in range(altura):
        fila.append((0, y))
        fila.append((largura - 1, y))

    while fila:
        x, y = fila.popleft()
        if not (0 <= x < largura and 0 <= y < altura):
            continue
        if fundo_visitado[y][x]:
            continue

        r, g, b, _ = pixels[x, y]
        if distancia_cor((r, g, b), COR_FUNDO_BEGE) <= tolerancia_flood:
            fundo_visitado[y][x] = True
            pixels[x, y] = (0, 0, 0, 0)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < largura and 0 <= ny < altura and not fundo_visitado[ny][nx]:
                    fila.append((nx, ny))

    # Limpeza suave de halo apenas nos pixels de contorno imediatamente adjacentes ao fundo externo
    ajustes: List[Tuple[int, int, Tuple[int, int, int, int]]] = []
    for y in range(altura):
        for x in range(largura):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            vizinhos_fundo = 0
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < largura and 0 <= ny < altura) or fundo_visitado[ny][nx]:
                    vizinhos_fundo += 1

            if vizinhos_fundo > 0:
                dist = distancia_cor((r, g, b), COR_FUNDO_BEGE)
                if dist < tolerancia_halo:
                    fator = max(0.0, (dist - 6.0) / (tolerancia_halo - 6.0))
                    novo_alpha = int(a * fator)
                    if novo_alpha < 30:
                        ajustes.append((x, y, (0, 0, 0, 0)))
                    else:
                        ajustes.append((x, y, (r, g, b, novo_alpha)))

    for x, y, novo_val in ajustes:
        pixels[x, y] = novo_val

    return rgba


def processar_celula(folha: Image.Image, linha: int, coluna: int, nome_orig: str) -> Image.Image:
    """Recorta uma célula da folha, remove rótulos/fundo/halo e aplica trim do bbox opaco."""
    x0 = coluna * LARGURA_CELULA
    y0 = linha * ALTURA_CELULA
    celula = folha.crop((x0, y0, x0 + LARGURA_CELULA, y0 + ALTURA_CELULA))

    min_y, max_y = LIMITES_Y_ESPECIFICOS.get(nome_orig, (3, 136))
    # Mantém margem lateral de 2px para evitar linhas de vizinhos
    area_util = celula.crop((2, min_y, LARGURA_CELULA - 2, max_y))

    limpa = remover_fundo_e_halo(area_util, tolerancia_flood=11.5, tolerancia_halo=28.0)

    # Faz o trim pela caixa delimitadora dos pixels com alpha > 16
    canal_alpha = limpa.split()[3].point(lambda a: 255 if a > 16 else 0)
    bbox = canal_alpha.getbbox()
    if bbox:
        # Adiciona 2px de respiro transparente ao redor se possível
        bx0 = max(0, bbox[0] - 2)
        by0 = max(0, bbox[1] - 2)
        bx1 = min(limpa.width, bbox[2] + 2)
        by1 = min(limpa.height, bbox[3] + 2)
        limpa = limpa.crop((bx0, by0, bx1, by1))

    return limpa


def gerar_contact_sheet(sprites_gerados: List[Tuple[str, Image.Image]]) -> None:
    """Monta `tools/contact_sheet.png` em fundo xadrez escuro para fácil inspeção visual."""
    colunas_cs = 6
    linhas_cs = math.ceil(len(sprites_gerados) / colunas_cs)
    larg_cel = 210
    alt_cel = 190
    folha_cs = Image.new("RGBA", (colunas_cs * larg_cel, linhas_cs * alt_cel), (38, 42, 52, 255))
    desenho = ImageDraw.Draw(folha_cs)
    fonte = ImageFont.load_default()

    for idx, (nome_arquivo, img_sprite) in enumerate(sprites_gerados):
        col = idx % colunas_cs
        lin = idx // colunas_cs
        cx = col * larg_cel
        cy = lin * alt_cel

        # Desenha quadriculado sutil para evidenciar transparência RGBA
        tam_quad = 14
        for qy in range(cy + 8, cy + alt_cel - 28, tam_quad):
            for qx in range(cx + 8, cx + larg_cel - 8, tam_quad):
                cor_q = (54, 58, 70, 255) if ((qx // tam_quad + qy // tam_quad) % 2 == 0) else (44, 48, 58, 255)
                desenho.rectangle([qx, qy, qx + tam_quad, qy + tam_quad], fill=cor_q)

        # Redimensiona apenas se exceder a caixa de visualização da contact sheet
        max_w, max_h = larg_cel - 24, alt_cel - 44
        copia = img_sprite.copy()
        copia.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        px = cx + (larg_cel - copia.width) // 2
        py = cy + 8 + (max_h - copia.height) // 2
        folha_cs.alpha_composite(copia, (px, py))

        desenho.rectangle([cx + 2, cy + 2, cx + larg_cel - 3, cy + alt_cel - 3], outline=(90, 98, 115, 255), width=1)
        desenho.text((cx + 10, cy + alt_cel - 20), nome_arquivo, fill=(235, 240, 248, 255), font=fonte)

    CAMINHO_CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    folha_cs.save(CAMINHO_CONTACT_SHEET)


def main() -> int:
    if not CAMINHO_REF1.exists():
        raise FileNotFoundError(f"Arquivo de referência não encontrado: {CAMINHO_REF1}")

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    folha = Image.open(CAMINHO_REF1).convert("RGB")

    sprites_gerados: List[Tuple[str, Image.Image]] = []
    for linha, coluna, nome_orig, nome_saida in MAPA_CELULAS:
        sprite_rgba = processar_celula(folha, linha, coluna, nome_orig)
        caminho_saida = PASTA_SAIDA / nome_saida
        sprite_rgba.save(caminho_saida, format="PNG")
        sprites_gerados.append((nome_saida, sprite_rgba))

    # Também cria alias basket_moving_01.png a partir de basket_leaves_01.png (compatibilidade PRD §14.1)
    caminho_leaves = PASTA_SAIDA / "basket_leaves_01.png"
    caminho_moving = PASTA_SAIDA / "basket_moving_01.png"
    if caminho_leaves.exists():
        Image.open(caminho_leaves).save(caminho_moving, format="PNG")

    gerar_contact_sheet(sprites_gerados)
    print(f"Recorte concluído: {len(sprites_gerados)} sprites salvos em {PASTA_SAIDA}")
    print(f"Contact sheet gerada em {CAMINHO_CONTACT_SHEET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
