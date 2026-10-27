"""Pong em Pygame — parte 3/5 — parte-03-bola-colisao
Sem assets externos: tudo desenhado com pygame.draw e fonte padrão.
Rode com:  python main.py
"""
import random
import pygame

LARGURA, ALTURA = 800, 500
FPS = 60
COR_FUNDO = (15, 15, 25)
COR_OBJ = (235, 235, 235)
VEL_RAQUETE = 380  # pixels por segundo
VEL_BOLA = 300

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Pong")
relogio = pygame.time.Clock()

esquerda = pygame.Rect(30, ALTURA // 2 - 45, 12, 90)
direita = pygame.Rect(LARGURA - 42, ALTURA // 2 - 45, 12, 90)
bola = pygame.Rect(LARGURA // 2 - 8, ALTURA // 2 - 8, 16, 16)
vx, vy = VEL_BOLA, VEL_BOLA * 0.6
bx, by = float(bola.x), float(bola.y)  # posição real em float (precisão com dt)


def sacar(direcao):
    """Recoloca a bola no centro e lança para a direção (+1 direita, -1 esquerda)."""
    global vx, vy, bx, by
    bx, by = LARGURA / 2 - 8, ALTURA / 2 - 8
    vx = VEL_BOLA * direcao
    vy = VEL_BOLA * random.uniform(-0.7, 0.7)


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

    if True:  # na parte 4 vira: if vencedor is None
        bx += vx * dt
        by += vy * dt
        bola.topleft = (round(bx), round(by))
        # rebate no topo e no fundo
        if bola.top <= 0 or bola.bottom >= ALTURA:
            vy = -vy
            by = min(max(by, 0), ALTURA - bola.height)
        # rebate nas raquetes: inverte E reposiciona (senão a bola "gruda")
        if bola.colliderect(esquerda) and vx < 0:
            vx = -vx
            bx = esquerda.right
        if bola.colliderect(direita) and vx > 0:
            vx = -vx
            bx = direita.left - bola.width
        # saiu pela lateral
        if bola.right < 0:
            sacar(1)
        if bola.left > LARGURA:
            sacar(-1)

    # 3) DESENHAR
    tela.fill(COR_FUNDO)
    pygame.draw.line(tela, (70, 70, 90), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 2)
    pygame.draw.rect(tela, COR_OBJ, esquerda)
    pygame.draw.rect(tela, COR_OBJ, direita)
    pygame.draw.ellipse(tela, COR_OBJ, bola)
    pygame.display.flip()

pygame.quit()
