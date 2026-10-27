# Egg Game — Parallax infinito com Pygame-CE

Protótipo **desktop** com os sprites e a paisagem do projeto Egg Game: De Volta ao Ninho.

## Iniciar (Linux, Windows ou macOS)

Com Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Na versão do Pygame-CE, o módulo importado continua sendo `pygame`.

## Controles

| Tecla | Ação |
|---|---|
| Enter / Espaço (menu) | Iniciar |
| A / D ou ← / → | Mover o ovo |
| Salto | Automático ao aterrissar |
| P ou Espaço (jogando) | Pausar / retomar |
| R | Recomeçar |
| Esc | Menu (ou sair a partir do menu) |
| 1 / 2 / 3 / 4 | Ligar/desligar céu, montanhas, vilarejo, árvore |
| H | Exibir hitboxes |
| F1 | Exibir coordenada da câmera, FPS e quantidade de cestas |
| F12 | Salvar captura.png na pasta do projeto |

## Organização

- `assets/background/sky.jpg`: céu, sem vilarejo nem árvore.
- `assets/background/mountains.png`: montanhas em camada com transparência suavizada.
- `assets/background/village.png`: cidade e rio em outra camada.
- `assets/tree/trunk_repeat.png`: textura de casca tornada verticalmente contínua para o protótipo.
- `assets/tree/trunk_A..G.png`: 7 recortes decorativos de tronco e folhas.
- `assets/egg/`: quadros do ovo (parado, subindo, descendo, quebrando).
- `assets/nests/`: sprites das cestas fixas, móveis, pequenas e frágeis.

## O que torna o cenário infinito?

`draw_tree()` repete `trunk_repeat.png` apenas na faixa visível da câmera e sobrepõe os módulos `trunk_A..G` a cada 300 unidades, de maneira determinística. O tronco não precisa existir como uma imagem gigantesca; suas posições são derivadas da coordenada global. `generate_until()` produz cestas acima do que a câmera está mostrando, e as antigas são descartadas.

As **camadas do panorama não se repetem**: o vilarejo e as montanhas descem devagar e desaparecem do quadro à medida que o ovo sobe. Assim não surge uma segunda igreja no céu. O céu é a camada de fundo presente o tempo todo.

## Limitações intencionais

- Protótipo de arquitetura visual e física, **não jogo final**.
- O encaixe decorativo de alguns módulos pode exibir pequenos artefatos: os sprites vêm de uma prancha conceitual, não de uma textura profissionalmente pintada para tile.
- Os recortes de panorama usam máscaras suavizadas, não reconstrução perfeita de pixels oclusos.
- Cestas geradas com distâncias moderadas, mas ainda não há **validador matemático completo de alcançabilidade**, próprio de produção.
- Não há Android nem controles por toque neste protótipo.
- Para testar, instale `pygame-ce`: esta demonstração **não depende** de PIL ou NumPy em tempo de execução.
