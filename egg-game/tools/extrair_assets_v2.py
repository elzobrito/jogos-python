#!/usr/bin/env python3
"""Extrai e prepara os assets visuais v2 (720x1280) a partir de ref/v2/.

Gera em assets/bg/:
- bg_vale.png (720x1280): fundo pintado de vale, vilarejo, montanhas e céu (paralaxe distante)
- bg_tronco_esq.png (240x1280 RGBA): tronco texturizado à esquerda com degraus e hera (paralaxe média)
- bg_copa_topo.png (720x180 RGBA): copa de folhas e galho superior
- galho_esq.png / galho_dir.png (RGBA): galhos laterais para apoiar cestas
- cesta_v2_normal.png, cesta_v2_folhas.png, cesta_v2_gelo.png, cesta_v2_musgo.png
- hud_placa_altura.png, hud_placa_recorde.png, hud_btn_pausa.png: placas de madeira limpas para texto dinâmico
- tela_menu_base.png, tela_modo_base.png, tela_comojogar_base.png, tela_pausa_base.png,
  tela_pausa_painel.png, tela_gameover_base.png, tela_vitoria_base.png, tela_opcoes_base.png
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


ROOT_DIR = Path(__file__).resolve().parent.parent
REF_V2_DIR = ROOT_DIR / "ref" / "v2"
OUT_DIR = ROOT_DIR / "assets" / "bg"


def sharpen_portrait(im: Image.Image) -> Image.Image:
    """Aplica nitidez suave para compensar o upscale de telas_retrato.png."""
    im_sharp = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=115, threshold=2))
    return ImageEnhance.Contrast(im_sharp).enhance(1.03)


def feather_paste(
    dst: Image.Image,
    src: Image.Image,
    box: tuple[int, int],
    feather_px: int = 12,
) -> None:
    """Cola `src` em `dst` na posição `box` com bordas suavizadas."""
    w, h = src.size
    mask = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(mask)
    for i in range(feather_px):
        alpha = int(255 * (i + 1) / (feather_px + 1))
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(1, feather_px // 2)))
    dst.paste(src, box, mask)


def feather_paste_vertical(
    dst: Image.Image,
    src: Image.Image,
    y_pos: int,
    feather_top: int = 40,
) -> None:
    """Cola uma faixa de largura total com transição suave apenas no topo."""
    w, h = src.size
    mask = Image.new("L", (w, h), 255)
    if feather_top > 0:
        arr = np.full((h, w), 255, dtype=np.uint8)
        for y in range(min(h, feather_top)):
            arr[y, :] = int(255 * (y + 1) / (feather_top + 1))
        mask = Image.fromarray(arr, mode="L").filter(ImageFilter.GaussianBlur(radius=4))
    dst.paste(src, (0, y_pos), mask)


def erase_wood_digits(
    im: Image.Image,
    rect: tuple[int, int, int, int],
    sample_box: tuple[int, int, int, int],
) -> None:
    """Apaga dígitos em placa de madeira usando amostra limpa da própria placa."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    clean_patch = im.crop(sample_box).resize((w, h), Image.Resampling.BILINEAR)
    clean_patch = clean_patch.filter(ImageFilter.GaussianBlur(radius=1.8))
    feather_paste(im, clean_patch, (x0, y0), feather_px=5)


def erase_parchment_content(
    im: Image.Image,
    rect: tuple[int, int, int, int],
) -> None:
    """Apaga apenas tinta/setas sobre pergaminho preservando 100% da textura original ao redor."""
    x0, y0, x1, y1 = rect
    crop_im = im.crop(rect)
    sub = np.array(crop_im, dtype=np.float32)
    h, w, _ = sub.shape

    # Detecta qualquer pixel que não seja pergaminho claro (letras, contornos, setas azuis/brancas)
    is_ink = (
        (sub[:, :, 0] < 228)
        | (sub[:, :, 1] < 198)
        | (sub[:, :, 2] < 146)
        | (sub[:, :, 2] > 202)
        | ((sub[:, :, 2] > sub[:, :, 1] - 10) & (sub[:, :, 0] < 235))
    )
    ink_mask_im = Image.fromarray((is_ink.astype(np.uint8) * 255), mode="L")
    # Dilata a máscara em 6px para cobrir halos anti-alias e suaviza bordas
    dilated_mask = ink_mask_im.filter(ImageFilter.MaxFilter(13)).filter(
        ImageFilter.GaussianBlur(radius=2.5)
    )

    is_clean_paper = np.array(dilated_mask) < 16
    if is_clean_paper.sum() >= 20:
        paper_color = np.median(sub[is_clean_paper], axis=0)
    else:
        paper_color = np.array([245.0, 222.0, 182.0], dtype=np.float32)

    rng = np.random.default_rng(42)
    noise = rng.normal(0.0, 1.0, size=(h, w, 3)).astype(np.float32)
    clean_paper_arr = np.clip(paper_color[None, None, :] + noise, 0, 255).astype(np.uint8)
    clean_paper_im = Image.fromarray(clean_paper_arr, mode=im.mode).filter(
        ImageFilter.GaussianBlur(radius=1.0)
    )

    im.paste(clean_paper_im, (x0, y0), dilated_mask)


def build_bg_vale(gm: Image.Image) -> Image.Image:
    """Constrói bg_vale.png (720x1280) 100% livre de cestas compondo faixas horizontais limpas."""
    canvas = Image.new("RGB", (720, 1280))

    # 1. Céu azul + nuvens fofas (x=830..1160, y=250..375 é 100% céu e nuvens sem cestas nem folhas)
    band_sky = gm.crop((830, 250, 1160, 375)).resize((720, 430), Image.Resampling.LANCZOS)
    canvas.paste(band_sky, (0, 0))

    # 2. Montanhas distantes azuis + colinas verdes (x=775..972, y=372..548 é 100% montanhas sem cestas)
    band_mountains = gm.crop((775, 372, 972, 548)).resize((720, 320), Image.Resampling.LANCZOS)
    feather_paste_vertical(canvas, band_mountains, 360, feather_top=65)

    # 3. Vale médio com igreja, chalés e pinheiros (x=1085..1400, y=538..775 é 100% cenário limpo)
    band_church = gm.crop((1085, 538, 1400, 775)).resize((720, 360), Image.Resampling.LANCZOS)
    feather_paste_vertical(canvas, band_church, 600, feather_top=75)

    # 4. Vilarejo inferior com rio, casas e árvores (x=830..1400, y=932..1122 é 100% cenário limpo)
    band_village = gm.crop((830, 932, 1400, 1122)).resize((720, 400), Image.Resampling.LANCZOS)
    feather_paste_vertical(canvas, band_village, 880, feather_top=75)

    return sharpen_portrait(canvas)


def build_bg_tronco_esq(gm: Image.Image) -> Image.Image:
    """Constrói bg_tronco_esq.png (240x1280 RGBA) com casca de árvore, degraus de madeira e hera."""
    # Amostras 100% limpas do tronco sem cestas nem HUD em gm (1402x1122):
    strip_a = gm.crop((95, 468, 345, 592)).resize((240, 320), Image.Resampling.LANCZOS)
    strip_b = gm.crop((190, 200, 412, 310)).resize((240, 260), Image.Resampling.LANCZOS)
    strip_c = gm.crop((60, 955, 275, 1118)).resize((240, 380), Image.Resampling.LANCZOS)

    trunk_canvas = Image.new("RGB", (240, 1280))
    trunk_canvas.paste(strip_a, (0, 0))
    feather_paste_vertical(trunk_canvas, strip_b, 270, feather_top=45)
    feather_paste_vertical(trunk_canvas, strip_a, 490, feather_top=45)
    feather_paste_vertical(trunk_canvas, strip_c, 770, feather_top=45)
    feather_paste_vertical(trunk_canvas, strip_a, 1060, feather_top=45)

    # Máscara alpha orgânica na borda direita (x=175..240) simulando casca e folhas
    arr = np.array(trunk_canvas)
    h, w, _ = arr.shape
    alpha = np.full((h, w), 255, dtype=np.uint8)
    y_coords = np.arange(h, dtype=np.float32)
    edge_x = (
        192.0
        + 10.0 * np.sin(y_coords / 65.0)
        + 6.0 * np.cos(y_coords / 27.0)
    ).astype(np.int32)

    for y in range(h):
        ex = int(edge_x[y])
        for x in range(ex, w):
            dist = x - ex
            a = max(0, int(255 * (1.0 - dist / 20.0)))
            alpha[y, x] = a

    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=2.0))
    trunk_rgba = trunk_canvas.convert("RGBA")
    trunk_rgba.putalpha(alpha_img)
    return trunk_rgba


def build_bg_copa_topo(gm: Image.Image) -> Image.Image:
    """Extrai a copa de folhas e galho superior (720x180 RGBA)."""
    crop = gm.crop((330, 0, 1030, 130)).resize((720, 180), Image.Resampling.LANCZOS)
    arr = np.array(crop)
    r = arr[:, :, 0].astype(np.float32)
    g = arr[:, :, 1].astype(np.float32)
    b = arr[:, :, 2].astype(np.float32)

    is_sky = (b > r + 12) & (b > g - 8) & (b > 135)
    alpha = np.where(is_sky, 0, 255).astype(np.uint8)
    for y in range(135, 180):
        factor = max(0.0, 1.0 - (y - 135) / 44.0)
        alpha[y, :] = (alpha[y, :] * factor).astype(np.uint8)

    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=1.8))
    rgba = crop.convert("RGBA")
    rgba.putalpha(alpha_img)
    return rgba


def extract_branch_and_baskets(gm: Image.Image) -> dict[str, Image.Image]:
    """Extrai galhos e cestas pintadas de gameplay_mockup.png com fundo transparente."""
    results: dict[str, Image.Image] = {}

    def cutout_element(box: tuple[int, int, int, int], out_size: tuple[int, int]) -> Image.Image:
        sub = gm.crop(box).convert("RGBA")
        arr = np.array(sub)
        h, w, _ = arr.shape
        r = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        b = arr[:, :, 2].astype(np.float32)
        visited = np.zeros((h, w), dtype=bool)
        queue: list[tuple[int, int]] = []
        for x in range(w):
            queue.append((0, x))
            queue.append((h - 1, x))
        for y in range(h):
            queue.append((y, 0))
            queue.append((y, w - 1))

        def is_bg(py: int, px: int) -> bool:
            pr, pg, pb = r[py, px], g[py, px], b[py, px]
            if pb > pr + 8 and pb > 115:
                return True
            if pr > 185 and pg > 205 and pb > 215:
                return True
            if (px < 12 or px > w - 13 or py < 10 or py > h - 11) and pb > 95 and pg > pr:
                return True
            return False

        while queue:
            cy, cx = queue.pop()
            if visited[cy, cx]:
                continue
            if not is_bg(cy, cx):
                continue
            visited[cy, cx] = True
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                    queue.append((ny, nx))

        alpha = np.where(visited, 0, 255).astype(np.uint8)
        alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=1.0))
        sub.putalpha(alpha_img)
        return sub.resize(out_size, Image.Resampling.LANCZOS)

    results["cesta_v2_normal.png"] = cutout_element((706, 130, 920, 222), (140, 62))
    results["cesta_v2_folhas.png"] = cutout_element((338, 272, 524, 378), (144, 76))
    results["cesta_v2_musgo.png"] = cutout_element((974, 380, 1218, 484), (148, 68))
    results["cesta_v2_gelo.png"] = cutout_element((822, 560, 1048, 672), (144, 74))

    galho_esq = cutout_element((295, 805, 535, 900), (220, 84))
    results["galho_esq.png"] = galho_esq
    results["galho_dir.png"] = galho_esq.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return results


def build_hud_plaques(p4: Image.Image) -> dict[str, Image.Image]:
    """Extrai as placas de madeira do HUD (ALTURA, RECORDE e botão Pausa) limpas para números dinâmicos."""
    p4_work = p4.copy()
    # Em p4, "ALTURA"/"RECORDE" terminam em y=84 e "0125 m"/"0450 m" começam em y=91..152
    erase_wood_digits(p4_work, (36, 86, 202, 160), sample_box=(44, 56, 62, 82))
    erase_wood_digits(p4_work, (474, 86, 608, 158), sample_box=(478, 56, 494, 82))

    def make_rounded_plaque(box: tuple[int, int, int, int]) -> Image.Image:
        crop = p4_work.crop(box).convert("RGBA")
        w, h = crop.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([2, 2, w - 3, h - 3], radius=18, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=1.0))
        crop.putalpha(mask)
        return crop

    return {
        "hud_placa_altura.png": make_rounded_plaque((20, 16, 214, 178)),
        "hud_placa_recorde.png": make_rounded_plaque((454, 18, 622, 174)),
        "hud_btn_pausa.png": make_rounded_plaque((624, 20, 706, 158)),
    }


def build_portrait_screens(
    tr: Image.Image,
    tt: Image.Image,
    hud_plaques: dict[str, Image.Image],
) -> dict[str, Image.Image]:
    """Extrai e limpa as 7 telas retrato de UI (720x1280) seguindo telas_retrato.png."""
    screens: dict[str, Image.Image] = {}

    # 1. Tela 1 - Menu inicial (Substitui "JUMP" em y=342..496 por "GAME" de tela_titulo.png)
    p1 = sharpen_portrait(tr.crop((5, 3, 407, 502)).resize((720, 1280), Image.Resampling.LANCZOS))
    erase_wood_digits(p1, (195, 340, 505, 496), sample_box=(185, 350, 208, 470))
    # Em tt, "GAME" está exatamente em x=1074..1520, y=253..383
    game_word = tt.crop((1074, 253, 1520, 383)).resize((310, 154), Image.Resampling.LANCZOS)
    feather_paste(p1, game_word, (195, 342), feather_px=8)
    screens["tela_menu_base.png"] = p1

    # 2. Tela 2 - Seleção de modo
    p2 = sharpen_portrait(tr.crop((419, 3, 791, 502)).resize((720, 1280), Image.Resampling.LANCZOS))
    screens["tela_modo_base.png"] = p2

    # 3. Tela 3 - Como jogar (remove setas laterais e textos antigos para desenhar mecânica §0)
    p3 = sharpen_portrait(tr.crop((803, 3, 1073, 502)).resize((720, 1280), Image.Resampling.LANCZOS))
    # Linha 1: seta esquerda (x=55..136, y=252..352) e seta direita (x=242..330, y=252..352)
    erase_parchment_content(p3, (55, 252, 136, 352))
    erase_parchment_content(p3, (242, 252, 330, 352))
    # Linha 3: setas azuis laterais (x=80..272, y=705..770)
    erase_parchment_content(p3, (80, 705, 272, 770))
    # Limpa os 4 blocos de texto à direita (x=340..658), preservando "COMO JOGAR" (y <= 210)
    erase_parchment_content(p3, (340, 222, 658, 395))
    erase_parchment_content(p3, (340, 425, 658, 602))
    erase_parchment_content(p3, (340, 685, 658, 880))
    erase_parchment_content(p3, (340, 905, 658, 1042))
    screens["tela_comojogar_base.png"] = p3

    # 4. Tela 5 - Pausa (limpa os dígitos "0125 m" e "0450 m" abaixo de "ALTURA"/"RECORDE" em y=86..160)
    p5 = sharpen_portrait(tr.crop((7, 535, 377, 984)).resize((720, 1280), Image.Resampling.LANCZOS))
    erase_wood_digits(p5, (40, 86, 204, 160), sample_box=(44, 56, 62, 82))
    erase_wood_digits(p5, (472, 86, 608, 158), sample_box=(478, 56, 494, 82))
    screens["tela_pausa_base.png"] = p5

    pausa_painel = p5.crop((168, 180, 566, 974)).convert("RGBA")
    screens["tela_pausa_painel.png"] = pausa_painel

    # 5. Tela 6 - Game Over (preserva "ALTURA"/"RECORDE" em y=670..726 e limpa "0125 m"/"0450 m" em y=732..830)
    p6 = sharpen_portrait(tr.crop((389, 535, 770, 984)).resize((720, 1280), Image.Resampling.LANCZOS))
    erase_parchment_content(p6, (125, 732, 348, 832))
    erase_parchment_content(p6, (402, 732, 618, 832))
    screens["tela_gameover_base.png"] = p6

    # 6. Tela 7 - Vitória (preserva "ALTURA"/"RECORDE" em y=790..836 e limpa "0125 m"/"0450 m" em y=838..938)
    p7 = sharpen_portrait(tr.crop((782, 535, 1147, 984)).resize((720, 1280), Image.Resampling.LANCZOS))
    erase_parchment_content(p7, (155, 838, 362, 938))
    erase_parchment_content(p7, (395, 838, 602, 938))
    screens["tela_vitoria_base.png"] = p7

    # 7. Tela 8 - Opções (remove "Inverter controles" com setas laterais em y=602..695)
    p8 = sharpen_portrait(tr.crop((1159, 535, 1528, 984)).resize((720, 1280), Image.Resampling.LANCZOS))
    erase_parchment_content(p8, (88, 602, 535, 695))
    screens["tela_opcoes_base.png"] = p8

    return screens


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gm = Image.open(REF_V2_DIR / "gameplay_mockup.png").convert("RGB")
    tr = Image.open(REF_V2_DIR / "telas_retrato.png").convert("RGB")
    tt = Image.open(REF_V2_DIR / "tela_titulo.png").convert("RGB")

    p4 = sharpen_portrait(tr.crop((1086, 3, 1528, 502)).resize((720, 1280), Image.Resampling.LANCZOS))

    bg_vale = build_bg_vale(gm)
    bg_vale.save(OUT_DIR / "bg_vale.png")

    bg_tronco = build_bg_tronco_esq(gm)
    bg_tronco.save(OUT_DIR / "bg_tronco_esq.png")

    bg_copa = build_bg_copa_topo(gm)
    bg_copa.save(OUT_DIR / "bg_copa_topo.png")

    for name, img in extract_branch_and_baskets(gm).items():
        img.save(OUT_DIR / name)

    hud_plaques = build_hud_plaques(p4)
    for name, img in hud_plaques.items():
        img.save(OUT_DIR / name)

    for name, img in build_portrait_screens(tr, tt, hud_plaques).items():
        img.save(OUT_DIR / name)

    print(f"Assets v2 gerados com sucesso em {OUT_DIR}:")
    for p in sorted(OUT_DIR.glob("*.png")):
        im = Image.open(p)
        print(f" - {p.name}: {im.size} {im.mode}")


if __name__ == "__main__":
    main()
