"""Snake em Pygame — parte 1/5 — parte-01-janela-loop
Rode com:  python main.py
"""
import pygame
import sys

pygame.init()

LARGURA = 800
ALTURA = 600
PRETO = (20, 20, 20)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake em Python")
relogio = pygame.time.Clock()

rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    tela.fill(PRETO)
    pygame.display.update()
    relogio.tick(8)

pygame.quit()
sys.exit()
