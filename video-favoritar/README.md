# Vídeo da Wiki: favoritar um estabelecimento

Fonte do vídeo da pergunta "Como favoritar um estabelecimento?", no mesmo
formato do piloto (direto, sem abertura, telas do app 2.0, narração e legenda).

- `roteiro-favoritar.md`: frases da narração e telas usadas
- `fig/`: telas exportadas do Figma (App ComproPay 2, seção "Favoritar"), 1x
- `build.py`: monta o vídeo e gera a legenda `.vtt`

A fonte, o modelo de voz e o venv ficam em `../video-comum` — veja o README
de lá para montar numa máquina nova. A saída vai para `out/` e é copiada à mão
para `ComproPay Wiki/videos/`.

```
../video-comum/.venv/bin/python build.py
```

`--prever` salva um quadro a cada meio segundo em `out/`, para conferir a
animação sem abrir o vídeo.

## Por que o build.py daqui não é o do piloto

O `video-piloto/build.py` foi escrito numa máquina Linux: ele chama `ffmpeg` do
PATH e carrega a Inter de `/usr/share/fonts/opentype/inter/`. Nenhum dos dois
existe no Mac. Este usa o ffmpeg do `imageio-ffmpeg`, que vem junto no venv.

O resto do desenho — tamanho, aparelho, gradiente, texto lateral, toques,
transições — é o mesmo, de propósito: os vídeos precisam parecer um só.
