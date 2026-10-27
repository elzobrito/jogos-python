# Sudoku

Sudoku didático em **Python + Pygame** (pygame-ce). Um único `main.py`, gerador com solução única e três dificuldades. Feito para as aulas do Elzo.

## Como rodar

```bash
cd ~/desenvolvimento/jogos/sudoku
python3 main.py
```

Demo (auto-solve + screenshots):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 main.py --demo
```

Teste do gerador:

```bash
python3 main.py --test
```

## Controles

| Tecla | Ação |
|-------|------|
| Clique / setas | Selecionar célula |
| 1–9 | Preencher |
| 0 / Backspace | Apagar |
| H | Dica |
| D | Ciclar dificuldade e gerar novo |
| N | Novo puzzle |
| R | Reset (mantém givens) |
| ESC | Sair |

## O que tem no jogo

- Grade branca com bordas 3×3 grossas
- Givens em negrito; entradas do jogador em azul
- Célula selecionada azul escuro; linha/coluna/bloco em azul claro
- Conflitos em vermelho
- Gerador por backtracking com verificação de unicidade
- Dificuldades: fácil / médio / difícil
- Mensagem de vitória ao completar

## Conceitos usados em aula

- Backtracking / recursão
- Validação de restrições (linha, coluna, bloco)
- Contagem de soluções para garantir unicidade
- Estado de UI e eventos de teclado/mouse
