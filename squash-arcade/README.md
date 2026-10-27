# Squash Arcade — Pong + som

Um exercício intermediário entre Pong e Breakout para aulas com **pygame-ce**.

## Executar

```bash
python -m pip install pygame-ce
python squash.py
```

**Mantenha a pasta `sons/` no mesmo diretório de `squash.py`.** Os efeitos já estão incluídos.

## Controles

- **← / → ou A / D:** mover a raquete
- **Espaço / Enter:** iniciar uma bola ou continuar após perder vida
- **P:** pausar / retomar
- **R:** reiniciar
- **M:** ligar/desligar som

## Como jogar

Impeça a bola de atravessar o piso. Cada rebatida na raquete soma **10 pontos**. A cada cinco rebatidas, são concedidos **25 pontos extras**. Você dispõe de três vidas. A bola acelera após cada rebatida.

## Objetivos pedagógicos

1. **Revisão de Pong:** `dt`, velocidade em pixels/segundo, reflexão, leitura de teclado.
2. **Novo conteúdo:** `pygame.mixer.pre_init`, `pygame.mixer.Sound`, reprodução de WAV, canais de som e volume.
3. **Preparação para Breakout:** contato com colisões entre bola e raquete, priorizando a detecção vertical da superfície de rebatida.

## Atividade proposta

- Substitua o som da parede por outro WAV.
- Faça a rebatida na raquete produzir um som agudo ou grave conforme o ponto de contato.
- Adicione um botão para controlar o volume.
- Mostre como a aplicação continua executando o game loop enquanto o som toca.

A geração procedural de som **não está no código**: neste momento os estudantes apenas carregam e reproduzem arquivos WAV. Síntese de áudio fica para uma etapa posterior da trilha de estudos.
