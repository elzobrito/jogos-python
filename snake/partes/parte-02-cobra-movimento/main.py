"""Snake em Pygame — parte 2/5 — parte-02-cobra-movimento
Rode com:  python main.py
"""
import pygame
import sys

pygame.init()

LARGURA = 800
ALTURA = 600
TAMANHO = 20
PRETO = (20, 20, 20)
VERDE = (0, 255, 0)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake em Python")
relogio = pygame.time.Clock()

cobra = [
    [400, 300],
    [380, 300],
    [360, 300]
]

velocidade_x = TAMANHO
velocidade_y = 0

rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                velocidade_x = 0
                velocidade_y = -TAMANHO
            elif evento.key == pygame.K_DOWN:
                velocidade_x = 0
                velocidade_y = TAMANHO
            elif evento.key == pygame.K_LEFT:
                velocidade_x = -TAMANHO
                velocidade_y = 0
            elif evento.key == pygame.K_RIGHT:
                velocidade_x = TAMANHO
                velocidade_y = 0

    cabeca = cobra[0]
    nova_cabeca = [
        cabeca[0] + velocidade_x,
        cabeca[1] + velocidade_y
    ]
    cobra.insert(0, nova_cabeca)
    cobra.pop()

    tela.fill(PRETO)
    for bloco in cobra:
        pygame.draw.rect(
            tela,
            VERDE,
            (bloco[0], bloco[1], TAMANHO, TAMANHO)
        )
    pygame.display.update()
    relogio.tick(8)

pygame.quit()
sys.exit()
