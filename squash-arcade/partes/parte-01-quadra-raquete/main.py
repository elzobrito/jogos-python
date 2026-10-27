"""Squash Arcade — parte 1/5 — quadra e raquete (reaproveitando o Pong).
Sem bola e sem som ainda. Rode com: python3 main.py
"""
from __future__ import annotations

import pygame

LARGURA, ALTURA = 900, 650
FPS = 60
CAMPO = pygame.Rect(55, 125, 790, 460)
RAQUETE_LARGURA, RAQUETE_ALTURA = 118, 18
VELOCIDADE_RAQUETE = 560

FUNDO = (12, 20, 36)
PAINEL = (23, 39, 62)
CAMPO_COR = (15, 29, 48)
GRADE = (32, 49, 72)
TEXTO = (235, 244, 255)
SUAVE = (151, 174, 200)
CIANO = (43, 221, 243)
VERDE = (67, 227, 157)


def escrever(tela, texto, fonte, cor, x, y, *, centro=False):
    img = fonte.render(texto, True, cor)
    retangulo = img.get_rect()
    if centro:
        retangulo.center = (x, y)
    else:
        retangulo.topleft = (x, y)
    tela.blit(img, retangulo)


def main() -> None:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Squash Arcade | Parte 1 — Quadra e raquete")
    fonte_titulo = pygame.font.SysFont("dejavusans", 27, bold=True)
    fonte_pequena = pygame.font.SysFont("dejavusans", 15)
    relogio = pygame.time.Clock()

    raquete = pygame.Rect(0, CAMPO.bottom - 40, RAQUETE_LARGURA, RAQUETE_ALTURA)
    raquete.centerx = CAMPO.centerx

    executando = True
    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.033)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

        teclas = pygame.key.get_pressed()
        direcao = int(bool(teclas[pygame.K_RIGHT] or teclas[pygame.K_d])) - int(
            bool(teclas[pygame.K_LEFT] or teclas[pygame.K_a])
        )
        raquete.x += round(direcao * VELOCIDADE_RAQUETE * dt)
        raquete.left = max(CAMPO.left + 6, raquete.left)
        raquete.right = min(CAMPO.right - 6, raquete.right)

        tela.fill(FUNDO)
        pygame.draw.rect(tela, PAINEL, (0, 0, LARGURA, 93))
        escrever(tela, "SQUASH ARCADE — PARTE 1", fonte_titulo, TEXTO, 55, 25)
        escrever(tela, "só a quadra e a raquete", fonte_pequena, SUAVE, 55, 58)

        pygame.draw.rect(tela, CAMPO_COR, CAMPO, border_radius=8)
        for x in range(CAMPO.left + 40, CAMPO.right, 40):
            pygame.draw.line(tela, GRADE, (x, CAMPO.top + 2), (x, CAMPO.bottom - 2))
        for y in range(CAMPO.top + 40, CAMPO.bottom, 40):
            pygame.draw.line(tela, GRADE, (CAMPO.left + 2, y), (CAMPO.right - 2, y))
        pygame.draw.rect(tela, (68, 100, 135), CAMPO, 2, border_radius=8)

        pygame.draw.rect(tela, VERDE, raquete, border_radius=7)
        pygame.draw.rect(
            tela, CIANO,
            (raquete.x + 7, raquete.y + 3, raquete.width - 14, 3),
            border_radius=2,
        )
        escrever(
            tela, "← → / A D  mover     ESC / X  sair",
            fonte_pequena, SUAVE, 60, 610,
        )
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
