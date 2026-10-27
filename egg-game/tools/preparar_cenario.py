#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepara o cenário e os assets visuais polidos do Round 3 (SPEC.md §11 + protótipo Elzo):

1. Árvore sem costuras em `assets/tree/`:
   - Copia e aprimora `trunk_repeat.png` (300x420 RGBA, 100% contínuo verticalmente) de
     `ref/impl_elzo/egg_game_pygame_ce/assets/tree/trunk_repeat.png`, preenchendo furos internos
     de chaveamento com casca escura.
   - Copia e aprimora os 7 módulos decorativos `trunk_A.png` .. `trunk_G.png`, removendo
     fragmentos soltos de borda (como a faixa superior residual de `trunk_G`), preenchendo
     buracos internos de nós (knotholes) com casca escura, aplicando defringe contra halos
     claros e suavizando o alpha no topo/base e na transição lateral com `trunk_repeat.png`
     para eliminar qualquer costura horizontal ou degrau lateral.
   - Mantém também `tronco_{base,a,b,c,topo}.png`, `galhos/` e `folhas/` (`folhas_01..04.png`).

2. Fundo de paralaxe em `assets/backgrounds/`:
   - Copia/adapta `sky.jpg`, `mountains.png` e `village.png` de
     `ref/impl_elzo/egg_game_pygame_ce/assets/background/` e gera as faixas correspondentes
     `ceu.png`, `nuvens.png`, `montanhas.png` e `vilarejo.png` para 720x1280.

3. Cestas e Ovo em alta nitidez (`assets/sprites/`):
   - Atualiza as cestas (`basket_static_01.png`, `basket_leaves_01.png`, `basket_fragile_01.png`, etc.)
     e quadros do ovo a partir de `ref/impl_elzo/egg_game_pygame_ce/assets/{nests,egg}/` após
     remover ilhas residuais desconectadas nas bordas do recorte.

4. Gera `tools/teste_tronco.png` demonstrando o tiling contínuo de `trunk_repeat.png` +
   sobreposição periódica determinística de `trunk_A..G.png` + folhas sem costura horizontal.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
import math
import shutil
import numpy as np
from PIL import Image, ImageFilter


ROOT_DIR = Path(__file__).resolve().parent.parent
REF_V3_DIR = ROOT_DIR / "ref" / "v3"
ELZO_ASSETS_DIR = ROOT_DIR / "ref" / "impl_elzo" / "egg_game_pygame_ce" / "assets"

BG_OUT_DIR = ROOT_DIR / "assets" / "backgrounds"
TREE_OUT_DIR = ROOT_DIR / "assets" / "tree"
GALHOS_OUT_DIR = TREE_OUT_DIR / "galhos"
FOLHAS_OUT_DIR = TREE_OUT_DIR / "folhas"
SPRITES_OUT_DIR = ROOT_DIR / "assets" / "sprites"
TESTE_TRONCO_PATH = ROOT_DIR / "tools" / "teste_tronco.png"


def remove_disconnected_border_islands(im: Image.Image, alpha_thresh: int = 20) -> Image.Image:
    """
    Mantém o componente conectado principal do sprite e remove pequenos fragmentos
    desconectados que tocam as bordas do recorte (ex.: ponta de cesta vizinha ou folha solta).
    """
    arr = np.array(im.convert("RGBA"), dtype=np.uint8)
    h, w, _ = arr.shape
    mask = arr[:, :, 3] >= alpha_thresh
    visited = np.zeros((h, w), dtype=bool)
    components: list[list[tuple[int, int]]] = []

    for y in range(h):
        for x in range(w):
            if mask[y, x] and not visited[y, x]:
                comp: list[tuple[int, int]] = []
                q: deque[tuple[int, int]] = deque([(y, x)])
                visited[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    comp.append((cy, cx))
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            q.append((ny, nx))
                components.append(comp)

    if not components:
        return im

    main_comp = max(components, key=len)
    main_len = len(main_comp)

    keep_mask = np.zeros((h, w), dtype=bool)
    for comp in components:
        if comp is main_comp:
            for cy, cx in comp:
                keep_mask[cy, cx] = True
            continue
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        touches_border = (min(ys) <= 2) or (max(ys) >= h - 3) or (min(xs) <= 2) or (max(xs) >= w - 3)
        # Se for um fragmento menor que 18% do principal tocando a borda, descarta
        if touches_border and len(comp) < main_len * 0.18:
            continue
        # Se for micro-ruído isolado (< 45 px), descarta
        if len(comp) < 45:
            continue
        for cy, cx in comp:
            keep_mask[cy, cx] = True

    # Suaviza 1px a máscara mantida para não deixar serrilhado
    keep_pil = Image.fromarray((keep_mask.astype(np.uint8) * 255), mode="L").filter(
        ImageFilter.MaxFilter(3)
    )
    arr[:, :, 3] = np.minimum(arr[:, :, 3], np.array(keep_pil, dtype=np.uint8))
    return Image.fromarray(arr, mode="RGBA")


def fill_internal_holes_and_defringe(im: Image.Image) -> Image.Image:
    """
    Preenche buracos transparentes ou brancos internos (knotholes) que não se conectam
    ao fundo externo com cor de casca escura `(50, 30, 15, 255)` e remove halos claros nas bordas.
    """
    arr = np.array(im.convert("RGBA"), dtype=np.uint8)
    h, w, _ = arr.shape

    is_bg_candidate = arr[:, :, 3] < 180
    ext_bg = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((0, x))
        q.append((h - 1, x))
    for y in range(h):
        q.append((y, 0))
        q.append((y, w - 1))

    while q:
        cy, cx = q.popleft()
        if ext_bg[cy, cx] or not is_bg_candidate[cy, cx]:
            continue
        ext_bg[cy, cx] = True
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not ext_bg[ny, nx]:
                q.append((ny, nx))

    # Qualquer pixel com alpha baixo que NÃO seja alcançável pelas bordas externas é um buraco interno
    internal_hole = (~ext_bg) & (arr[:, :, 3] < 245)
    if np.any(internal_hole):
        yy, xx = np.where(internal_hole)
        # Mistura suavemente com marrom escuro profundo de cavidade de árvore
        a_cur = arr[yy, xx, 3].astype(np.float32) / 255.0
        arr[yy, xx, 0] = np.clip(arr[yy, xx, 0] * a_cur + 48.0 * (1.0 - a_cur), 0, 255).astype(np.uint8)
        arr[yy, xx, 1] = np.clip(arr[yy, xx, 1] * a_cur + 28.0 * (1.0 - a_cur), 0, 255).astype(np.uint8)
        arr[yy, xx, 2] = np.clip(arr[yy, xx, 2] * a_cur + 14.0 * (1.0 - a_cur), 0, 255).astype(np.uint8)
        arr[yy, xx, 3] = 255

    # Defringe de pixels muito claros na borda externa
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    a = arr[:, :, 3].astype(np.int16)
    white_halo = (a > 0) & (r > 180) & (g > 175) & (b > 155)
    if np.any(white_halo):
        arr[white_halo, 0] = (arr[white_halo, 0].astype(np.uint16) * 52 // 100).astype(np.uint8)
        arr[white_halo, 1] = (arr[white_halo, 1].astype(np.uint16) * 50 // 100).astype(np.uint8)
        arr[white_halo, 2] = (arr[white_halo, 2].astype(np.uint16) * 40 // 100).astype(np.uint8)
        arr[white_halo, 3] = (arr[white_halo, 3].astype(np.uint16) * 40 // 100).astype(np.uint8)

    return Image.fromarray(arr, mode="RGBA")


def prepare_seamless_tree_elzo() -> None:
    """
    Prepara `trunk_repeat.png` e `trunk_A..G.png` em `assets/tree/` seguindo a arquitetura
    do protótipo Elzo, alinhando o cilindro de todos os módulos `trunk_A..G` exatamente
    sobre a silhueta contínua de `trunk_repeat.png` para eliminar qualquer costura horizontal
    ou degrau lateral contra o céu.
    """
    TREE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    GALHOS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    FOLHAS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. `trunk_repeat.png` (300x420 RGBA): corrige o furo interno e uniformiza a largura
    #    horizontal da casca para que o tiling vertical seja 100% contínuo e sem degraus
    tr_raw = Image.open(ELZO_ASSETS_DIR / "tree" / "trunk_repeat.png").convert("RGBA")
    tr_clean = fill_internal_holes_and_defringe(tr_raw)
    tr_arr = np.array(tr_clean, dtype=np.float32)
    h_tr, w_tr, _ = tr_arr.shape

    # Limpa os pixels corrompidos dentro do nó escuro em x=25..70, y=145..220
    sub_box = tr_arr[145:220, 25:70]
    bad_glitch = (sub_box[:, :, 0] < 35) | ((sub_box[:, :, 0] > 150) & (sub_box[:, :, 2] < 45))
    sub_box[bad_glitch, 0] = 52.0
    sub_box[bad_glitch, 1] = 31.0
    sub_box[bad_glitch, 2] = 16.0
    sub_box[bad_glitch, 3] = 255.0
    tr_arr[145:220, 25:70] = sub_box

    # Faz crossfade vertical periódico nos 36px do topo/base de `trunk_repeat`
    tr_orig = tr_arr.copy()
    blend_h = 36
    for y in range(blend_h):
        # Na linha y=0, mistura 50/50 com a linha y=h_tr-1; em y=blend_h volta a 100% original
        t = (y + 0.5) / float(blend_h)
        w_cur = 0.5 + 0.5 * math.sin(0.5 * math.pi * t)
        opp_y = h_tr - 1 - y
        tr_arr[y] = w_cur * tr_orig[y] + (1.0 - w_cur) * tr_orig[opp_y]
        tr_arr[opp_y] = w_cur * tr_orig[opp_y] + (1.0 - w_cur) * tr_orig[y]

    # Perfil horizontal mestre de alpha do cilindro (garante que nenhum módulo vaze casca reta no céu)
    master_alpha_x = tr_arr[:, :, 3].min(axis=0) / 255.0  # (300,)

    trunk_repeat_im = Image.fromarray(np.clip(tr_arr, 0, 255).astype(np.uint8), mode="RGBA")
    trunk_repeat_im.save(TREE_OUT_DIR / "trunk_repeat.png")

    # 2. `trunk_A.png` .. `trunk_G.png` alinhados à largura [0..265] de `trunk_repeat.png` (largura 340px)
    # Deslocamento X para alinhar a borda direita do cilindro de cada peça em x=264
    cyl_right_map = {
        "A": 316,
        "B": 295,
        "C": 314,
        "D": 366,
        "E": 255,
        "F": 350,
        "G": 234,
    }
    target_right = 264
    out_w = 340

    for letter in "ABCDEFG":
        part_raw = Image.open(ELZO_ASSETS_DIR / "tree" / f"trunk_{letter}.png").convert("RGBA")
        if letter == "G":
            p_arr = np.array(part_raw)
            p_arr[:58, :, 3] = 0
            part_raw = Image.fromarray(p_arr, mode="RGBA")

        part_clean = remove_disconnected_border_islands(part_raw)
        part_clean = fill_internal_holes_and_defringe(part_clean)

        # Alinha horizontalmente no canvas de largura `out_w` (340x340)
        shift_x = target_right - cyl_right_map[letter]
        aligned = Image.new("RGBA", (out_w, part_clean.height), (0, 0, 0, 0))
        aligned.paste(part_clean, (shift_x, 0))
        arr = np.array(aligned, dtype=np.float32)
        h, w, _ = arr.shape

        # Identifica pixels verdes de folhagem e galhos laterais direitos (C e E)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        is_green_leaf = (g >= r - 6.0) & (g > b + 12.0)
        is_right_branch = np.zeros((h, w), dtype=bool)
        if letter == "C":
            is_right_branch[30:182, 245:] = True
        elif letter == "E":
            is_right_branch[25:228, 245:] = True

        # Envelope horizontal: dentro do cilindro usa master_alpha_x; folhas e galhos C/E podem sair à direita
        env_x = np.zeros((w,), dtype=np.float32)
        env_x[:w_tr] = master_alpha_x
        for y in range(h):
            for x in range(w):
                if not (is_green_leaf[y, x] or is_right_branch[y, x]):
                    arr[y, x, 3] *= env_x[x]

        # Fade vertical cosseno suave nas extremidades superior e inferior (72px)
        fade_v = 72
        for y in range(fade_v):
            s = 0.5 - 0.5 * math.cos(math.pi * (y / float(fade_v)))
            arr[y, :, 3] *= s
        for idx in range(fade_v):
            y = h - 1 - idx
            s = 0.5 - 0.5 * math.cos(math.pi * (idx / float(fade_v)))
            arr[y, :, 3] *= s

        part_out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGBA")
        part_out.save(TREE_OUT_DIR / f"trunk_{letter}.png")

    trunk_repeat_im.save(TREE_OUT_DIR / "tronco_base.png")
    shutil.copyfile(TREE_OUT_DIR / "trunk_A.png", TREE_OUT_DIR / "tronco_a.png")
    shutil.copyfile(TREE_OUT_DIR / "trunk_B.png", TREE_OUT_DIR / "tronco_b.png")
    shutil.copyfile(TREE_OUT_DIR / "trunk_C.png", TREE_OUT_DIR / "tronco_c.png")
    shutil.copyfile(TREE_OUT_DIR / "trunk_E.png", TREE_OUT_DIR / "tronco_topo.png")


def prepare_backgrounds() -> None:
    """
    Copia `sky.jpg`, `mountains.png` e `village.png` de `ref/impl_elzo/egg_game_pygame_ce/assets/background/`
    e gera `ceu.png`, `nuvens.png`, `montanhas.png` e `vilarejo.png` em `assets/backgrounds/`.
    """
    BG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ("sky.jpg", "mountains.png", "village.png"):
        shutil.copyfile(ELZO_ASSETS_DIR / "background" / fname, BG_OUT_DIR / fname)

    # Também mantém `ceu.png`, `nuvens.png`, `montanhas.png` e `vilarejo.png` (720px de largura)
    src = Image.open(REF_V3_DIR / "paisagem_limpa.png").convert("RGB")
    crop_x0, crop_x1 = 1120, 2920

    sky_sample = np.array(
        src.crop((1450, 20, 2250, 420)).resize((720, 320), Image.Resampling.LANCZOS),
        dtype=np.float32,
    )
    sky_row_colors = np.percentile(sky_sample, 25, axis=1)
    half_h = 320
    t_vals = np.linspace(0.0, 1.0, half_h, dtype=np.float32)[:, None]
    top_blue = np.array([28.0, 134.0, 238.0], dtype=np.float32)
    mid_blue = np.median(sky_row_colors, axis=0).astype(np.float32)
    half_grad = top_blue[None, :] * (1.0 - t_vals) + mid_blue[None, :] * t_vals
    full_grad = np.vstack([half_grad, half_grad[::-1]])
    sky_arr = np.repeat(full_grad[:, None, :], 720, axis=1).astype(np.uint8)
    Image.fromarray(sky_arr, mode="RGB").convert("RGBA").save(BG_OUT_DIR / "ceu.png")

    clouds_crop = src.crop((220, 0, 2220, 820)).resize((720, 560), Image.Resampling.LANCZOS)
    c_arr = np.array(clouds_crop, dtype=np.float32)
    r = c_arr[:, :, 0]
    whiteness = np.clip((r - 45.0) / 155.0, 0.0, 1.0)
    cloud_alpha = np.clip((whiteness ** 1.15) * 255.0, 0.0, 255.0)
    h_c = 560
    y_idx = np.arange(h_c, dtype=np.float32)
    feather_top = np.clip(y_idx / 75.0, 0.0, 1.0)
    feather_bot = np.clip((h_c - 1 - y_idx) / 95.0, 0.0, 1.0)
    cloud_alpha = (cloud_alpha * feather_top[:, None] * feather_bot[:, None]).astype(np.uint8)
    cloud_alpha_im = Image.fromarray(cloud_alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=2.0))
    nuvens_im = clouds_crop.convert("RGBA")
    nuvens_im.putalpha(cloud_alpha_im)
    nuvens_im.save(BG_OUT_DIR / "nuvens.png")

    # Montanhas e vilarejo usando os recortes suaves do protótipo Elzo adaptados para 720px
    elzo_mtn = Image.open(ELZO_ASSETS_DIR / "background" / "mountains.png").convert("RGBA")
    elzo_vil = Image.open(ELZO_ASSETS_DIR / "background" / "village.png").convert("RGBA")
    # Recorta a janela rica da igreja/lago/montanhas (x=140..1080 -> 720px)
    elzo_mtn.crop((140, 0, 1080, elzo_mtn.height)).resize((720, 360), Image.Resampling.LANCZOS).save(
        BG_OUT_DIR / "montanhas.png"
    )
    elzo_vil.crop((140, 0, 1080, elzo_vil.height)).resize((720, 480), Image.Resampling.LANCZOS).save(
        BG_OUT_DIR / "vilarejo.png"
    )


def upgrade_baskets_and_egg_sprites() -> None:
    """
    Atualiza as cestas e os sprites do ovo em `assets/sprites/` com as versões de maior
    resolução de `ref/impl_elzo/egg_game_pygame_ce/assets/{nests,egg}/`, removendo
    quaisquer ilhas residuais nas bordas.
    """
    SPRITES_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cestas de maior nitidez (limpando pequenos fragmentos de borda)
    nest_map = {
        "fixa_01.png": ["basket_static_01.png"],
        "folhas_01.png": ["basket_leaves_01.png", "basket_leaves_02.png"],
        "movel_01.png": ["basket_moving_01.png", "basket_ice_01.png", "basket_ice_02.png"],
        "fragil_01.png": ["basket_fragile_01.png", "basket_fake_01.png"],
        "elastica_01.png": ["basket_cloud_01.png"],
    }
    for src_name, dst_names in nest_map.items():
        src_path = ELZO_ASSETS_DIR / "nests" / src_name
        if src_path.exists():
            cleaned = remove_disconnected_border_islands(Image.open(src_path))
            # Trim para a caixa opaca limpa
            arr = np.array(cleaned)
            ys, xs = np.where(arr[:, :, 3] > 20)
            if len(xs) > 0:
                cleaned = cleaned.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
            for dst_name in dst_names:
                cleaned.save(SPRITES_OUT_DIR / dst_name)

    # Quadros do ovo em maior resolução (limpando fragmentos de borda)
    egg_groups = [
        ("idle", 5, "egg_idle_0{i}.png"),
        ("jump", 6, "egg_jump_0{i}.png"),
        ("fall", 4, "egg_fall_0{i}.png"),
        ("death", 4, "egg_death_0{i}.png"),
    ]
    for prefix, count, dst_pattern in egg_groups:
        for i in range(count):
            src_path = ELZO_ASSETS_DIR / "egg" / f"{prefix}_{i + 1:02d}.png"
            if src_path.exists():
                cleaned = remove_disconnected_border_islands(Image.open(src_path))
                arr = np.array(cleaned)
                ys, xs = np.where(arr[:, :, 3] > 20)
                if len(xs) > 0:
                    cleaned = cleaned.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
                cleaned.save(SPRITES_OUT_DIR / dst_pattern.format(i=i))


def generate_teste_tronco() -> None:
    """
    Gera `tools/teste_tronco.png` (720x1280) demonstrando a arquitetura de árvore do Round 3:
    tiling contínuo de `trunk_repeat.png` + sobreposição periódica determinística de `trunk_A..G.png`
    + tufos de folhas sobre o vale pintado, sem nenhuma costura horizontal.
    """
    w, h = 720, 1280
    canvas = Image.new("RGBA", (w, h), (96, 185, 247, 255))

    sky = Image.open(BG_OUT_DIR / "sky.jpg").convert("RGBA")
    # Preenche o céu em 720x1280
    sky_top = sky.crop((120, 0, 840, 720))
    sky_bot = sky.crop((120, 160, 840, 720))
    canvas.paste(sky_top, (0, 0))
    canvas.paste(sky_bot, (0, 720))

    mtn = Image.open(BG_OUT_DIR / "montanhas.png").convert("RGBA")
    vil = Image.open(BG_OUT_DIR / "vilarejo.png").convert("RGBA")
    canvas.alpha_composite(mtn, (0, 520))
    canvas.alpha_composite(vil, (0, 800))

    trunk_repeat = Image.open(TREE_OUT_DIR / "trunk_repeat.png").convert("RGBA")
    tree_parts = [
        Image.open(TREE_OUT_DIR / f"trunk_{c}.png").convert("RGBA")
        for c in "ABCDEFG"
    ]
    folhas = sorted(FOLHAS_OUT_DIR.glob("folhas_*.png"))
    folha_imgs = [Image.open(p).convert("RGBA") for p in folhas]

    # 1. Tiling contínuo de `trunk_repeat.png` (1.0x câmera)
    tr_h = trunk_repeat.height
    x_core = 0
    for y in range(-tr_h, h + tr_h, tr_h):
        canvas.alpha_composite(trunk_repeat, (x_core, y + 25))

    # 2. Sobreposição periódica determinística dos módulos `trunk_A..G.png` a cada 290px
    spacing = 290
    for idx, y in enumerate(range(-spacing, h + spacing, spacing)):
        part = tree_parts[idx % len(tree_parts)]
        px = x_core
        py = y + 10
        canvas.alpha_composite(part, (px, py))
        if folha_imgs:
            f_im = folha_imgs[idx % len(folha_imgs)]
            fx = x_core + 45 + ((idx * 43) % 95)
            fy = py + 24
            canvas.alpha_composite(f_im, (fx, fy))

    canvas.convert("RGB").save(TESTE_TRONCO_PATH)


def main() -> None:
    prepare_seamless_tree_elzo()
    prepare_backgrounds()
    upgrade_baskets_and_egg_sprites()
    generate_teste_tronco()
    print("Cenário e assets do Round 3 preparados com sucesso!")
    im_t = Image.open(TESTE_TRONCO_PATH)
    print(f" - {TESTE_TRONCO_PATH.relative_to(ROOT_DIR)}: {im_t.size} {im_t.mode}")


if __name__ == "__main__":
    main()
