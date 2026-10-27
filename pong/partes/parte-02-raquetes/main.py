"""Pong em Pygame — parte 2/5 — parte-02-raquetes
Sem assets externos: tudo desenhado com pygame.draw e fonte padrão.
Rode com:  python main.py
"""
import pygame

LARGURA, ALTURA = 800, 500
FPS = 60
COR_FUNDO = (15, 15, 25)
COR_OBJ = (235, 235, 235)
VEL_RAQUETE = 380  # pixels por segundo

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Pong")
relogio = pygame.time.Clock()

esquerda = pygame.Rect(30, ALTURA // 2 - 45, 12, 90)
direita = pygame.Rect(LARGURA - 42, ALTURA // 2 - 45, 12, 90)




def mover_raquete(r, cima, baixo, dt):
    teclas = pygame.key.get_pressed()
    if teclas[cima]:
        r.y -= int(VEL_RAQUETE * dt)
    if teclas[baixo]:
        r.y += int(VEL_RAQUETE * dt)
    r.clamp_ip(tela.get_rect())  # não deixa sair da tela




rodando = True
while rodando:
    dt = relogio.tick(FPS) / 1000  # segundos desde o último quadro

    # 1) EVENTOS
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # 2) ATUALIZAR
    mover_raquete(esquerda, pygame.K_w, pygame.K_s, dt)
    mover_raquete(direita, pygame.K_UP, pygame.K_DOWN, dt)


    # 3) DESENHAR
    tela.fill(COR_FUNDO)
    pygame.draw.line(tela, (70, 70, 90), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 2)
    pygame.draw.rect(tela, COR_OBJ, esquerda)
    pygame.draw.rect(tela, COR_OBJ, direita)
    pygame.display.flip()

pygame.quit()
