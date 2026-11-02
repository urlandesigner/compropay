# Vídeo da Wiki: favoritar um estabelecimento

Fonte do vídeo da pergunta "Como favoritar um estabelecimento?", no mesmo
formato do piloto (direto, sem abertura, telas do app 2.0, narração e legenda).

- `roteiro-favoritar.md`: frases da narração e telas usadas
- `fig/`: telas exportadas do Figma (App ComproPay 2, seção "Favoritar"), 1x
- `fonts/`: Inter, usada no texto lateral
- `build.py`: monta o vídeo e gera a legenda `.vtt`

A saída vai para `out/` e é copiada à mão para `ComproPay Wiki/videos/`.

## Rodar

Diferente do piloto, aqui o ambiente é todo local e não depende de nada
instalado no sistema — nem ffmpeg, que vem no `imageio-ffmpeg`.

```
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python pillow numpy soundfile qrcode imageio-ffmpeg kokoro-onnx
```

Falta só o modelo da voz, que não cabe no repositório (~350 MB). Baixe das
releases de `thewh1teagle/kokoro-onnx` para `tts/`:

```
curl -L -o tts/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o tts/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Depois:

```
.venv/bin/python build.py
```

`--prever` salva um quadro a cada meio segundo em `out/`, para conferir a
animação sem abrir o vídeo.

## Por que o build.py daqui não é o do piloto

O `video-piloto/build.py` foi escrito numa máquina Linux: ele chama `ffmpeg` do
PATH e carrega a Inter de `/usr/share/fonts/opentype/inter/`. Nenhum dos dois
existe no Mac. Este usa o ffmpeg do `imageio-ffmpeg` e a fonte de `fonts/`.

O resto do desenho — tamanho, aparelho, gradiente, texto lateral, toques,
transições — é o mesmo, de propósito: os dois vídeos precisam parecer um só.
