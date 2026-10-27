# Genius Musical — Sprite Pack (Flat)

Pacote visual para o jogo didático Genius Musical em Pygame-CE.

## Estrutura

- `icones/`: 4 ícones isolados em PNG RGBA transparente, 512 × 512 pixels.
- `botoes/`: 4 elementos × 4 estados (`normal`, `ativo`, `pressionado`, `desativado`), 512 × 512 pixels. Cantos dos cartões transparentes.
- `svg_editavel/`: fontes vetoriais correspondentes, escaláveis sem perda.
- `preview_genius.png`: prévia dos 16 botões.

## Cores e elementos

- Fogo: coral / vermelho (Dó4, 261,63 Hz)
- Água: azul (Mi4, 329,63 Hz)
- Terra: verde (Sol4, 392 Hz)
- Ar: amarelo (Dó5, 523,25 Hz)

## Uso no Pygame

```python
fogo = pygame.image.load('botoes/fogo_normal.png').convert_alpha()
fogo_ativo = pygame.image.load('botoes/fogo_ativo.png').convert_alpha()

fogo = pygame.transform.smoothscale(fogo, (180, 180))
tela.blit(fogo, (100, 100))
```

Arquivos `.png` de imagens; as notas musicais devem continuar sendo sintetizadas no código do jogo. Não há arquivos de áudio incluídos.
