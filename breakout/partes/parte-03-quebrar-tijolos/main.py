"""Breakout em Pygame — parte 3/5 — parte-03-quebrar-tijolos
Evolução do Pong: mesma raquete/bola, agora com tijolos. Sem assets externos.
Rode com:  python main.py
"""
import pygame

LARGURA, ALTURA = 800, 600
FPS = 60
COR_FUNDO = (15, 15, 25)
COR_OBJ = (235, 235, 235)
VEL_RAQUETE = 520
VEL_BOLA = 340
CORES_LINHAS = [(230, 80, 80), (240, 160, 60), (240, 220, 80), (90, 200, 120), (80, 150, 230)]
COLUNAS, LINHAS = 10, 5
TIJ_L, TIJ_A, ESPACO, TOPO = 72, 22, 6, 60

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Breakout")
relogio = pygame.time.Clock()
fonte = pygame.font.Font(None, 32)

raquete = pygame.Rect(LARGURA // 2 - 60, ALTURA - 40, 120, 14)
bola = pygame.Rect(0, 0, 14, 14)
bx = by = vx = vy = 0.0


def lancar_bola():
    """Bola em cima da raquete, subindo."""
    global bx, by, vx, vy
    bx, by = raquete.centerx - 7, raquete.top - 20
    vx, vy = VEL_BOLA * 0.6, -VEL_BOLA


def criar_tijolos():
    tijolos = []
    x0 = (LARGURA - (COLUNAS * TIJ_L + (COLUNAS - 1) * ESPACO)) // 2
    for lin in range(LINHAS):
        for col in range(COLUNAS):
            r = pygame.Rect(x0 + col * (TIJ_L + ESPACO), TOPO + lin * (TIJ_A + ESPACO), TIJ_L, TIJ_A)
            tijolos.append({"rect": r, "cor": CORES_LINHAS[lin]})
    return tijolos


def rebater_no_tijolo(r):
    """Decide o lado da colisão pela MENOR sobreposição e inverte o eixo certo."""
    global vx, vy, bx, by
    sobre_x = min(bola.right - r.left, r.right - bola.left)
    sobre_y = min(bola.bottom - r.top, r.bottom - bola.top)
    if sobre_x < sobre_y:  # bateu na lateral
        vx = -vx
        bx += -sobre_x if bola.centerx < r.centerx else sobre_x
    else:  # bateu em cima ou embaixo
        vy = -vy
        by += -sobre_y if bola.centery < r.centery else sobre_y




lancar_bola()
tijolos = criar_tijolos()
pontos = 0

rodando = True
while rodando:
    dt = relogio.tick(FPS) / 1000

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    if True:  # na parte 4 vira: if estado == "JOGANDO"
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            raquete.x -= int(VEL_RAQUETE * dt)
        if teclas[pygame.K_RIGHT]:
            raquete.x += int(VEL_RAQUETE * dt)
        raquete.clamp_ip(tela.get_rect())

        bx += vx * dt
        by += vy * dt
        bola.topleft = (round(bx), round(by))
        if bola.left <= 0 or bola.right >= LARGURA:
            vx = -vx
            bx = min(max(bx, 0), LARGURA - bola.width)
        if bola.top <= 0:
            vy = abs(vy)
            by = 0
        if bola.colliderect(raquete) and vy > 0:
            vy = -abs(vy)
            by = raquete.top - bola.height
        if bola.top > ALTURA:  # caiu
            lancar_bola()

        i = bola.collidelist([t["rect"] for t in tijolos])
        if i != -1:
            rebater_no_tijolo(tijolos[i]["rect"])
            tijolos.pop(i)  # remove fora de qualquer for: seguro
            pontos += 10

    tela.fill(COR_FUNDO)
    for t in tijolos:
        pygame.draw.rect(tela, t["cor"], t["rect"], border_radius=3)
    pygame.draw.rect(tela, COR_OBJ, raquete, border_radius=4)
    pygame.draw.ellipse(tela, COR_OBJ, bola)
    tela.blit(fonte.render(f"Pontos: {pontos}", True, COR_OBJ), (12, 12))
    pygame.display.flip()

pygame.quit()
