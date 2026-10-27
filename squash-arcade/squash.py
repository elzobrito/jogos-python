"""Squash Arcade — exercício intermediário entre Pong e Breakout.

Dependência: python -m pip install pygame-ce
Execução:    python squash.py

Objetivos didáticos:
    * Consolidar game loop, delta time e reflexão de velocidade (Pong).
    * Introduzir efeitos sonoros com pygame.mixer.Sound.
    * Usar canais para não interromper efeitos importantes.

Os efeitos são arquivos WAV na pasta sons/, não são gerados pelo jogo.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import pygame

# --- Configurações -----------------------------------------------
LARGURA, ALTURA = 900, 650
FPS = 60
CAMPO = pygame.Rect(55, 125, 790, 460)
RAQUETE_LARGURA, RAQUETE_ALTURA = 118, 18
VELOCIDADE_RAQUETE = 560  # pixels por segundo
RAIO = 11
VIDAS_INICIAIS = 3
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
VERMELHO = (255, 110, 128)

SONS = {
    "parede": "parede.wav",
    "raquete": "raquete.wav",
    "ponto": "ponto.wav",
    "vida": "vida.wav",
    "fim": "fim.wav",
}


class Audio:
    """Carrega WAVs e toca efeitos sem bloquear o game loop."""

    def __init__(self) -> None:
        self.ativo = True
        self.efeitos: dict[str, pygame.mixer.Sound] = {}
        self.disponivel = pygame.mixer.get_init() is not None
        if not self.disponivel:
            print("Áudio indisponível: jogo continuará sem efeitos.")
            return

        pasta = Path(__file__).resolve().parent / "sons"
        pygame.mixer.set_num_channels(8)
        for nome, arquivo in SONS.items():
            caminho = pasta / arquivo
            try:
                self.efeitos[nome] = pygame.mixer.Sound(str(caminho))
            except (FileNotFoundError, pygame.error) as erro:
                print(f"Som não carregado ({arquivo}): {erro}")

    def tocar(self, nome: str) -> None:
        if not self.disponivel or not self.ativo or nome not in self.efeitos:
            return
        # Canal 0: colisões frequentes. Canal 1: pontos e avisos.
        canal = pygame.mixer.Channel(0 if nome in ("parede", "raquete") else 1)
        canal.set_volume(0.30 if nome in ("parede", "raquete") else 0.56)
        canal.play(self.efeitos[nome])

    def alternar(self) -> None:
        self.ativo = not self.ativo
        if self.disponivel and not self.ativo:
            pygame.mixer.stop()


class Squash:
    def __init__(self, audio: Audio) -> None:
        self.audio = audio
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
        self.vidas = VIDAS_INICIAIS
        self.estado = "inicio"

    def soltar_bola(self) -> None:
        self.x, self.y = float(CAMPO.centerx), float(CAMPO.centery)
        self.velocidade = VELOCIDADE_INICIAL + min(self.rebatidas * 12, 190)
        angulo = math.radians(random.choice((-34, -26, 26, 34)))
        self.vx = math.sin(angulo) * self.velocidade
        self.vy = math.cos(angulo) * self.velocidade  # Começa descendo.
        self.estado = "jogando"

    def iniciar_ou_continuar(self) -> None:
        if self.estado in ("inicio", "vida_perdida"):
            self.soltar_bola()
        elif self.estado == "pausado":
            self.estado = "jogando"
        elif self.estado == "fim":
            self.zerar()
            self.soltar_bola()

    def perder_vida(self) -> None:
        self.vidas -= 1
        if self.vidas <= 0:
            self.estado = "fim"
            self.audio.tocar("fim")
        else:
            self.estado = "vida_perdida"
            self.audio.tocar("vida")

    def atualizar(self, dt: float, teclas: pygame.key.ScancodeWrapper) -> None:
        if self.estado != "jogando":
            return

        # Física da raquete, em pixels/segundo: independe da taxa de quadros.
        direcao = int(bool(teclas[pygame.K_RIGHT] or teclas[pygame.K_d])) - int(
            bool(teclas[pygame.K_LEFT] or teclas[pygame.K_a])
        )
        self.raquete.x += round(direcao * VELOCIDADE_RAQUETE * dt)
        self.raquete.left = max(CAMPO.left + 6, self.raquete.left)
        self.raquete.right = min(CAMPO.right - 6, self.raquete.right)

        anterior_y = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Reflexão nas paredes laterais e no teto (o chão não rebate).
        if self.x - RAIO < CAMPO.left:
            self.x = CAMPO.left + RAIO
            self.vx = abs(self.vx)
            self.audio.tocar("parede")
        elif self.x + RAIO > CAMPO.right:
            self.x = CAMPO.right - RAIO
            self.vx = -abs(self.vx)
            self.audio.tocar("parede")

        if self.y - RAIO < CAMPO.top:
            self.y = CAMPO.top + RAIO
            self.vy = abs(self.vy)
            self.audio.tocar("parede")

        # Raquete: detecta a passagem da borda inferior da bola pela borda
        # superior da raquete, quando a bola está descendo.
        cruzou_raquete = (self.vy > 0
                          and anterior_y + RAIO <= self.raquete.top
                          and self.y + RAIO >= self.raquete.top)
        sobre_raquete = (self.raquete.left - RAIO <= self.x <= self.raquete.right + RAIO)
        if cruzou_raquete and sobre_raquete:
            self.y = self.raquete.top - RAIO
            # Rebater perto das extremidades muda a direção (como no Pong).
            deslocamento = (self.x - self.raquete.centerx) / (self.raquete.width / 2)
            deslocamento = max(-1.0, min(1.0, deslocamento))
            angulo = math.radians(65 * deslocamento)
            self.velocidade = min(VELOCIDADE_MAXIMA, self.velocidade + 14)
            self.vx = self.velocidade * math.sin(angulo)
            self.vy = -self.velocidade * math.cos(angulo)
            self.rebatidas += 1
            self.pontos += 10
            self.audio.tocar("raquete")
            if self.rebatidas % 5 == 0:
                self.pontos += 25
                self.audio.tocar("ponto")

        # A bola atravessou a parte inferior do campo.
        if self.y - RAIO > CAMPO.bottom:
            self.perder_vida()


def escrever(tela: pygame.Surface, texto: str, fonte: pygame.font.Font,
             cor: tuple[int, int, int], x: int, y: int,
             *, centro: bool = False) -> None:
    img = fonte.render(texto, True, cor)
    retangulo = img.get_rect()
    if centro:
        retangulo.center = (x, y)
    else:
        retangulo.topleft = (x, y)
    tela.blit(img, retangulo)


def desenhar(tela: pygame.Surface, jogo: Squash,
             titulo: pygame.font.Font, normal: pygame.font.Font,
             pequeno: pygame.font.Font) -> None:
    tela.fill(FUNDO)
    pygame.draw.rect(tela, PAINEL, (0, 0, LARGURA, 93))
    escrever(tela, "SQUASH ARCADE", titulo, TEXTO, 55, 25)
    escrever(tela, f"PONTOS  {jogo.pontos}", normal, CIANO, 435, 37)
    escrever(tela, f"VIDAS  {jogo.vidas}", normal, VERDE, 673, 37)

    pygame.draw.rect(tela, CAMPO_COR, CAMPO, border_radius=8)
    for x in range(CAMPO.left + 40, CAMPO.right, 40):
        pygame.draw.line(tela, GRADE, (x, CAMPO.top + 2), (x, CAMPO.bottom - 2))
    for y in range(CAMPO.top + 40, CAMPO.bottom, 40):
        pygame.draw.line(tela, GRADE, (CAMPO.left + 2, y), (CAMPO.right - 2, y))
    pygame.draw.rect(tela, (68, 100, 135), CAMPO, 2, border_radius=8)

    # Raquete e bola possuem cores contrastantes.
    pygame.draw.rect(tela, VERDE, jogo.raquete, border_radius=7)
    pygame.draw.rect(tela, CIANO, (jogo.raquete.x + 7, jogo.raquete.y + 3,
                                  jogo.raquete.width - 14, 3), border_radius=2)
    pygame.draw.circle(tela, AMARELO, (round(jogo.x), round(jogo.y)), RAIO)
    pygame.draw.circle(tela, TEXTO, (round(jogo.x - 3), round(jogo.y - 3)), 3)

    escrever(tela, "← → / A D  mover     ESPAÇO  jogar     P  pausa     R  reiniciar     M  som",
             pequeno, SUAVE, 60, 610)
    estado_som = "SOM LIGADO" if jogo.audio.ativo and jogo.audio.disponivel else "SOM DESLIGADO"
    escrever(tela, estado_som, pequeno,
             VERDE if jogo.audio.ativo and jogo.audio.disponivel else VERMELHO,
             725, 610)

    avisos = {
        "inicio": ("PREPARE-SE", "Pressione ESPAÇO ou ENTER para começar"),
        "pausado": ("PAUSADO", "Pressione P ou ESPAÇO para continuar"),
        "vida_perdida": ("VOCÊ PERDEU UMA VIDA", "Pressione ESPAÇO para a próxima bola"),
        "fim": ("FIM DE JOGO", "Pressione R para jogar novamente"),
    }
    if jogo.estado in avisos:
        camada = pygame.Surface(CAMPO.size, pygame.SRCALPHA)
        camada.fill((5, 12, 25, 178))
        tela.blit(camada, CAMPO.topleft)
        caixa = pygame.Rect(CAMPO.centerx - 260, CAMPO.centery - 72, 520, 144)
        pygame.draw.rect(tela, PAINEL, caixa, border_radius=12)
        pygame.draw.rect(tela, CIANO, caixa, 2, border_radius=12)
        linha1, linha2 = avisos[jogo.estado]
        escrever(tela, linha1, titulo, TEXTO, caixa.centerx, caixa.top + 47, centro=True)
        escrever(tela, linha2, normal, SUAVE, caixa.centerx, caixa.top + 105, centro=True)


def main() -> None:
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Squash Arcade | Pong + Som")
    fonte_titulo = pygame.font.SysFont("dejavusans", 27, bold=True)
    fonte_normal = pygame.font.SysFont("dejavusans", 19, bold=True)
    fonte_pequena = pygame.font.SysFont("dejavusans", 15)
    relogio = pygame.time.Clock()

    jogo = Squash(Audio())
    executando = True
    while executando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.033)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    jogo.iniciar_ou_continuar()
                elif evento.key == pygame.K_p:
                    if jogo.estado == "jogando":
                        jogo.estado = "pausado"
                    elif jogo.estado == "pausado":
                        jogo.estado = "jogando"
                elif evento.key == pygame.K_r:
                    jogo.zerar()
                elif evento.key == pygame.K_m:
                    jogo.audio.alternar()
        jogo.atualizar(dt, pygame.key.get_pressed())
        desenhar(tela, jogo, fonte_titulo, fonte_normal, fonte_pequena)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
