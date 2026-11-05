# Montador de vídeos da Wiki

Um programa só (`montar.py`) no lugar de um `build.py` por vídeo. Cada vídeo
traz um `roteiro.yaml`: as telas, as frases e o que acontece em cada uma.
Narração (Kokoro), legenda `.vtt`, aparelho, transição, círculo de toque,
holofote, pôster e folha de revisão saem sozinhos.

```
video-comum/.venv/bin/python video-comum/montador/montar.py video-rede/roteiro.yaml
video-comum/.venv/bin/python video-comum/montador/montar.py video-rede/roteiro.yaml --so-revisao
```

A saída vai para `out/` ao lado do roteiro (ou `--saida`): `<video>.mp4`,
`<video>.vtt`, `<video>.jpg` (pôster), `narracao.wav` e `revisao.jpg`.

**Validado:** o roteiro de `video-rede/` gera o mesmo vídeo que o `build.py`
daquela pasta — legenda igual, áudio com diferença 0,0, quadros iguais pixel a
pixel e pôster idêntico byte a byte. Os `build.py` antigos continuam onde
estão; migre um vídeo por vez e confira do mesmo jeito.

## Regra antes de publicar: olhe a folha de revisão

`revisao.jpg` mostra cada tela **como vai aparecer no vídeo**, com as máscaras
contornadas em vermelho. Confira nome, saldo, final de cartão, notificação na
barra de cima. Só depois copie o vídeo para `ComproPay Wiki/videos/`. A Wiki é
pública: o que sai no vídeo sai para qualquer pessoa.

Rode `--so-revisao` primeiro: não gasta voz nem vídeo e já mostra se uma
máscara errou o alvo.

## Formato do roteiro

```yaml
video: rede-credenciada          # nome dos arquivos de saída
rotulo: Consultar a rede credenciada   # a linha pequena em roxo, acima da frase
voz: pf_dora                     # opcional (Kokoro)
aparelho: { largura: 430, altura: 896 }   # opcional; esse é o padrão

telas:
  home:
    fonte: fig/home.png          # relativa ao roteiro
    fixo_topo: 62                # com fixo_topo/fixo_base a tela é ROLÁVEL:
    fixo_base: 120               #   barra de cima e menu de baixo ficam parados
    fim_conteudo: 1152           #   até onde a rolagem pode ir
    focos:
      servicos: { rola: [848, 1136] }   # faixa em coordenadas da imagem
    mascara:
      - { rect: [20, 70, 220, 100], modo: borrar }
  rede:
    fonte: fig/rede.png          # 414 de largura? a diferença é completada sozinha
    focos:
      busca: [24, 91, 405, 143]  # retângulo fixo na tela do aparelho

passos:                          # um por frase da narração
  - fala: "Na tela inicial, role até Serviços."
    tela: home                   # só no primeiro passo; depois vale a tela de destino
    rolar: 370                   # quanto a tela rola neste passo
    foco: servicos               # nome, [x0,y0,x1,y1] ou { rola: [y0,y1] }
    pausa: 0.4                   # silêncio depois do passo (padrão 0,45)
  - fala: "Toque em Rede."
    toque: [60, 563]             # onde o círculo cai, na tela do aparelho, já rolada
    vai_para: rede               # a tela desliza para esta depois do toque
  - fala: "No topo, busque por nome, cidade ou bairro."
    foco: busca

poster: { passo: 4, apos: 1.0 }  # opcional; padrão: penúltimo passo, 1 s depois do começo
```

### Como o tempo é decidido

- A frase de cada passo é narrada em ordem; o que acontece nele é relativo a ela.
- `toque` cai 0,15 s depois que a frase termina. Para tocar no meio da fala:
  `toque: { em: [x, y], quando: 0.4 }` (segundos depois do começo da frase).
- `vai_para` desliza a tela 0,25 s depois do toque; o passo seguinte começa
  quando a transição acaba, mais a `pausa`.
- `rolar` leva 1,2 s e começa 0,15 s depois da frase. Com `rolar` e `foco` no
  mesmo passo, o holofote só acende depois da rolagem.
- Um holofote some quando o próximo entra (um cede ao outro), ou quando um
  passo sem `foco` e sem `toque` começa. Passo só com `toque` não apaga.

### Máscaras (dado pessoal)

Em `telas.<nome>.mascara`, retângulos na tela já com a largura do aparelho:

| modo | o que faz |
|---|---|
| `borrar` (padrão) | borra o retângulo (`raio`, padrão 10) |
| `cobrir` | tampa com cor lisa (`cor: [r,g,b]`) |
| `colar` | cola o mesmo retângulo de outra imagem (`de:`), útil com o Figma, que tem dados fictícios, quando o layout bate |

### Erros que o montador já pega

- Tela com altura diferente do aparelho e sem `fixo_topo`/`fixo_base`.
- Tela mais larga que o aparelho.
- Rolagem que passa do fim do conteúdo.

## Telas do iPhone misturadas com telas do Figma

O mesmo vídeo pode ter a home do Figma 2.0 e as telas seguintes direto do app
no iPhone (Espelhamento do iPhone, janela no tamanho máximo, 391x860). Para a
tela capturada:

```yaml
aparelho: { largura: 430, altura: 932 }        # a proporção do iPhone; a home do Figma (430x1255) rola dentro dele
telas:
  home:  { fonte: fig/home.png, fixo_topo: 62, fixo_base: 120, fim_conteudo: 1152 }
  lista:
    fonte: iphone/rede.png                      # o print da janela inteira, sem editar
    captura: true                               # recorta a margem, arredonda os cantos e ajusta à escala
    barra_status: { de: fig/home.png }          # troca hora e bateria reais por 9:41 limpo (altura 50)
```

O que `captura: true` faz: corta a margem branca da janela espelhada (a tela
útil é 376x814 dentro dos 391x860), tira o fio cinza da borda, preenche as fatias
fora do canto arredondado e estica para a largura do aparelho (cerca de 1,15x).
Se o tamanho da janela mudar, passe o recorte: `captura: { recorte: [x0, y0, x1, y1], raio: 44 }`.

`barra_status` pega só o desenho da barra da imagem de origem (hora, sinal, wifi,
bateria) e o coloca sobre a cor de fundo da própria tela, lida logo abaixo da barra.
A ilha dinâmica some junto. Vale para telas de **cabeçalho claro**; sobre cabeçalho
escuro os ícones ficariam escuros.

**Limites conhecidos**
- A captura tem ~376 px de largura útil e vai a 430: fica um pouco mais macia que
  uma tela do Figma exportada em 1x. Para nitidez total, tire o print no próprio
  iPhone (3x) e mande por AirDrop; o resto do fluxo é igual.
- Mascare nome, saldo e notificação na folha de revisão, como nas outras telas.

## Limites de hoje

- Uma tela por vez (sem várias janelas lado a lado).
- Digitação em campo não é animada: o jeito é ter duas imagens (vazio e
  preenchido) e uma troca de tela entre elas.
- O montador não captura nada. As telas vêm de `fig/`, exportadas do Figma ou
  tiradas do iPhone.
