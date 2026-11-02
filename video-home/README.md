# Vídeo: a tela inicial

Tour da tela inicial do App ComproPay 2, seção por seção. Ainda **não entrou em
nenhuma pergunta da Wiki**: as 28 que existem são todas "como fazer X", e um
tour é outro tipo de conteúdo. O arquivo está pronto em `out/` esperando
decisão.

- `roteiro-home.md`: frases da narração, as seções e os limites medidos no Figma
- `fig/home.png`: o frame `7276:89822`, 430x1255, exportado 1x
- `build.py`: monta o vídeo e a legenda `.vtt`

Para rodar, veja `../video-comum/README.md` — é de lá que vêm a fonte, o
modelo de voz e o Python. A saída vai para `out/`.

```
../video-comum/.venv/bin/python build.py
```

## Como a rolagem funciona

A tela do aparelho no vídeo tem 430x932, mas o frame tem 1255 de altura. A
barra de status fica fixa no topo, o menu inferior fica fixo no rodapé, e o
meio rola de 0 a 340.

Esse 340 custou uma versão: com 316, que era a conta exata até o fim dos
Serviços, a última fileira de rótulos (Vendas, Empréstimos, Doações, Ver todos)
encostava no menu e a caixa do holofote cortava as palavras no meio. Os 24px a
mais são a folga que existe embaixo do conteúdo.

## O fecho volta ao topo

A última frase tem rolagem 0 de propósito. Na primeira versão ela dizia "essa é
a tela inicial" com a tela ainda rolada no fim, mostrando o rodapé — dizia uma
coisa e mostrava outra.
