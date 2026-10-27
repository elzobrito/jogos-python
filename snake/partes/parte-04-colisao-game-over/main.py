"""Snake em Pygame — parte 4/5 — parte-04-colisao-game-over
Rode com:  python main.py
"""
import pygame
import sys
import random

pygame.init()

LARGURA = 800
ALTURA = 600
TAMANHO = 20
PRETO = (20, 20, 20)
VERDE = (50, 205, 50)
VERMELHO = (220, 50, 50)
BRANCO = (255, 255, 255)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake em Python")
fonte = pygame.font.SysFont("arial", 28)
fonte_grande = pygame.font.SysFont("arial", 50, bold=True)
relogio = pygame.time.Clock()


def gerar_comida():
    return [
        random.randrange(0, LARGURA, TAMANHO),
        random.randrange(0, ALTURA, TAMANHO)
    ]


def desenhar_cobra(cobra):
    for bloco in cobra:
        pygame.draw.rect(
            tela,
            VERDE,
            (bloco[0], bloco[1], TAMANHO, TAMANHO)
        )


def desenhar_comida(comida):
    pygame.draw.rect(
        tela,
        VERMELHO,
        (comida[0], comida[1], TAMANHO, TAMANHO)
    )


def desenhar_pontos(pontos):
    texto = fonte.render(f"Pontos: {pontos}", True, BRANCO)
    tela.blit(texto, (20, 20))


def game_over(pontos):
    while True:
        tela.fill(PRETO)
        msg = fonte_grande.render("GAME OVER", True, VERMELHO)
        tela.blit(msg, (280, 220))
        pts = fonte.render(f"Pontos: {pontos}", True, BRANCO)
        tela.blit(pts, (330, 300))
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


cobra = [
    [400, 300],
    [380, 300],
    [360, 300]
]
velocidade_x = TAMANHO
velocidade_y = 0
comida = gerar_comida()
pontos = 0
rodando = True

while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP and velocidade_y == 0:
                velocidade_x = 0
                velocidade_y = -TAMANHO
            elif evento.key == pygame.K_DOWN and velocidade_y == 0:
                velocidade_x = 0
                velocidade_y = TAMANHO
            elif evento.key == pygame.K_LEFT and velocidade_x == 0:
                velocidade_x = -TAMANHO
                velocidade_y = 0
            elif evento.key == pygame.K_RIGHT and velocidade_x == 0:
                velocidade_x = TAMANHO
                velocidade_y = 0

    cabeca = cobra[0]
    nova_cabeca = [
        cabeca[0] + velocidade_x,
        cabeca[1] + velocidade_y
    ]

    if (
        nova_cabeca[0] < 0
        or nova_cabeca[0] >= LARGURA
        or nova_cabeca[1] < 0
        or nova_cabeca[1] >= ALTURA
    ):
        rodando = False

    if nova_cabeca in cobra[1:]:
        rodando = False

    cobra.insert(0, nova_cabeca)

    if nova_cabeca == comida:
        comida = gerar_comida()
        pontos += 10
    else:
        cobra.pop()

    tela.fill(PRETO)
    desenhar_cobra(cobra)
    desenhar_comida(comida)
    desenhar_pontos(pontos)
    pygame.display.update()
    relogio.tick(8)

game_over(pontos)
