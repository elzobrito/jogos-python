"""Pong em Pygame — parte 1/5 — parte-01-janela-loop
Sem assets externos: tudo desenhado com pygame.draw e fonte padrão.
Rode com:  python main.py
"""
import pygame

LARGURA, ALTURA = 800, 500
FPS = 60
COR_FUNDO = (15, 15, 25)
COR_OBJ = (235, 235, 235)

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Pong")
relogio = pygame.time.Clock()









rodando = True
while rodando:
    dt = relogio.tick(FPS) / 1000  # segundos desde o último quadro

    # 1) EVENTOS
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # 2) ATUALIZAR


    # 3) DESENHAR
    tela.fill(COR_FUNDO)
    pygame.draw.line(tela, (70, 70, 90), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 2)
    pygame.display.flip()

pygame.quit()
