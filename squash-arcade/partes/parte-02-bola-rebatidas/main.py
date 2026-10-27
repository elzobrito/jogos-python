"""Squash Arcade — parte 2/5 — bola e rebatidas (ainda sem som).
Rode com: python3 main.py
"""
from __future__ import annotations

import math
import random

import pygame

LARGURA, ALTURA = 900, 650
FPS = 60
CAMPO = pygame.Rect(55, 125, 790, 460)
RAQUETE_LARGURA, RAQUETE_ALTURA = 118, 18
VELOCIDADE_RAQUETE = 560
RAIO = 11
VELOCIDADE_INICIAL = 340
VELOCIDADE_MAXIMA = 680

FUNDO = (12, 20, 36)
PAINEL = (23, 39, 62)
CAMPO_COR = (15, 29, 48)
GRADE = (32, 49, 72)
TEXTO = (235, 244, 255)
SUAVE = (151, 174, 200)
CIANO = (43, 221, 243)
VERDE = (67, 227, 157)
AMARELO = (255, 205, 76)


def escrever(tela, texto, fonte, cor, x, y, *, centro=False):
    img = fonte.render(texto, True, cor)
    retangulo = img.get_rect()
    if centro:
        retangulo.center = (x, y)
    else:
        retangulo.topleft = (x, y)
    tela.blit(img, retangulo)


class Squash:
    def __init__(self) -> None:
        self.raquete = pygame.Rect(0, CAMPO.bottom - 40,
                                  RAQUETE_LARGURA, RAQUETE_ALTURA)
        self.zerar()

    def zerar(self) -> None:
        self.raquete.centerx = CAMPO.centerx
        self.x, self.y = float(CAMPO.centerx), float(CAMPO.centery)
        self.vx, self.vy = 0.0, 0.0
        self.velocidade = VELOCIDADE_INICIAL
        self.pontos = 0
        self.rebatidas = 0
        self.estado = "inicio"

    def soltar_bola(self) -> None:
        self.x, self.y = float(CAMPO.centerx), float(CAMPO.centery)
        self.velocidade = VELOCIDADE_INICIAL + min(self.rebatidas * 12, 190)
        angulo = math.radians(random.choice((-34, -26, 26, 34)))
        self.vx = math.sin(angulo) * self.velocidade
        self.vy = math.cos(angulo) * self.velocidade
        self.estado = "jogando"

    def atualizar(self, dt: float, teclas) -> None:
        if self.estado != "jogando":
            return

        direcao = int(bool(teclas[pygame.K_RIGHT] or teclas[pygame.K_d])) - int(
            bool(teclas[pygame.K_LEFT] or teclas[pygame.K_a])
        )
        self.raquete.x += round(direcao * VELOCIDADE_RAQUETE * dt)
        self.raquete.left = max(CAMPO.left + 6, self.raquete.left)
        self.raquete.right = min(CAMPO.right - 6, self.raquete.right)

        anterior_y = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x - RAIO < CAMPO.left:
            self.x = CAMPO.left + RAIO
            self.vx = abs(self.vx)
        elif self.x + RAIO > CAMPO.right:
            self.x = CAMPO.right - RAIO
            self.vx = -abs(self.vx)

        if self.y - RAIO < CAMPO.top:
            self.y = CAMPO.top + RAIO
            self.vy = abs(self.vy)

        cruzou_raquete = (self.vy > 0
                          and anterior_y + RAIO <= self.raquete.top
                          and self.y + RAIO >= self.raquete.top)
        sobre_raquete = (self.raquete.left - RAIO <= self.x <= self.raquete.right + RAIO)
        if cruzou_raquete and sobre_raquete:
            self.y = self.raquete.top - RAIO
            deslocamento = (self.x - self.raquete.centerx) / (self.raquete.width / 2)
            deslocamento = max(-1.0, min(1.0, deslocamento))
            angulo = math.radians(65 * deslocamento)
            self.velocidade = min(VELOCIDADE_MAXIMA, self.velocidade + 14)
            self.vx = self.velocidade * math.sin(angulo)
            self.vy = -self.velocidade * math.cos(angulo)
            self.rebatidas += 1
            self.pontos += 10

        if self.y - RAIO > CAMPO.bottom:
            # Sem vidas ainda: só recoloca a bola no centro.
            self.estado = "inicio"
            self.vx, self.vy = 0.0, 0.0


def desenhar(tela, jogo, titulo, normal, pequeno):
    tela.fill(FUNDO)
    pygame.draw.rect(tela, PAINEL, (0, 0, LARGURA, 93))
    escrever(tela, "SQUASH ARCADE — PARTE 2", titulo, TEXTO, 55, 25)
    escrever(tela, f"PONTOS  {jogo.pontos}", normal, CIANO, 435, 37)

    pygame.draw.rect(tela, CAMPO_COR, CAMPO, border_radius=8)
    for x in range(CAMPO.left + 40, CAMPO.right, 40):
        pygame.draw.line(tela, GRADE, (x, CAMPO.top + 2), (x, CAMPO.bottom - 2))
    for y in range(CAMPO.top + 40, CAMPO.bottom, 40):
        pygame.draw.line(tela, GRADE, (CAMPO.left + 2, y), (CAMPO.right - 2, y))
    pygame.draw.rect(tela, (68, 100, 135), CAMPO, 2, border_radius=8)

    pygame.draw.rect(tela, VERDE, jogo.raquete, border_radius=7)
    pygame.draw.rect(tela, CIANO, (jogo.raquete.x + 7, jogo.raquete.y + 3,
                                  jogo.raquete.width - 14, 3), border_radius=2)
    pygame.draw.circle(tela, AMARELO, (round(jogo.x), round(jogo.y)), RAIO)
    pygame.draw.circle(tela, TEXTO, (round(jogo.x - 3), round(jogo.y - 3)), 3)

    escrever(tela, "← → / A D  mover     ESPAÇO  jogar     R  reiniciar",
             pequeno, SUAVE, 60, 610)
    if jogo.estado == "inicio":
        escrever(tela, "Pressione ESPAÇO para soltar a bola",
                 normal, SUAVE, CAMPO.centerx, CAMPO.centery - 40, centro=True)


def main() -> None:
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Squash Arcade | Parte 2 — Bola e rebatidas")
    fonte_titulo = pygame.font.SysFont("dejavusans", 27, bold=True)
    fonte_normal = pygame.font.SysFont("dejavusans", 19, bold=True)
    fonte_pequena = pygame.font.SysFont("dejavusans", 15)
    relogio = pygame.time.Clock()
    jogo = Squash()
    executando = True
    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.033)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if jogo.estado == "inicio":
                        jogo.soltar_bola()
                elif evento.key == pygame.K_r:
                    jogo.zerar()
        jogo.atualizar(dt, pygame.key.get_pressed())
        desenhar(tela, jogo, fonte_titulo, fonte_normal, fonte_pequena)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
