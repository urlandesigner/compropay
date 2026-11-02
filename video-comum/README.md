# O que os vídeos da Wiki compartilham

Cada vídeo mora na sua pasta (`video-cartao/`, `video-favoritar/`, …) com as
telas do Figma, o roteiro e o `build.py`. O que é pesado e igual para todos
fica aqui:

- `fonts/`: Inter (Regular, SemiBold, Bold), usada no texto lateral
- `tts/`: modelo do Kokoro — **não vai para o Git**, são 350 MB
- `.venv/`: Python 3.11 com pillow, numpy, soundfile, qrcode, kokoro-onnx e
  imageio-ffmpeg (o ffmpeg vem junto, não precisa instalar nada no sistema)

## Montar a pasta numa máquina nova

```
uv venv --python 3.11 video-comum/.venv
uv pip install --python video-comum/.venv/bin/python \
  pillow numpy soundfile qrcode imageio-ffmpeg kokoro-onnx

mkdir -p video-comum/tts && cd video-comum/tts
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

A Inter sai das releases de `rsms/inter`, em `extras/otf/`.

## Exportar as telas do Figma

O MCP do Figma corta por limite de chamadas (o time ComproCard é plano
Starter) e não avisa antes: ele para no meio de um fluxo. Quem não tem limite é
o plugin Desktop Bridge, que fala com o Figma aberto na máquina. Há dois
caminhos por ali, e os dois saem com os mesmos bytes — conferido num frame de
430x932, 98.490 bytes pelos dois.

**`figma_capture_screenshot`** é o caminho curto: não precisa de rede nem de
servidor, grava o PNG em disco e devolve o caminho no resultado. É só copiar o
arquivo para `fig/`. Duas pegadinhas: ele **devolve a imagem junto**, então
cada tela custa contexto, e ele **limita o lado maior a 1568px**. Para telas de
aparelho (430x932, 430x1255) isso não aperta; para exportar uma seção inteira
de uma vez, aperta.

**`figma_execute` com `exportAsync`** é o caminho para lote: roda em cada frame
e manda os bytes para um receptor HTTP local, sem imagem nenhuma no contexto e
sem limite de tamanho. O receptor é um servidor de 30 linhas. Duas coisas que
custam tempo quando não se sabe:

- O manifest do plugin libera `http://localhost`, **não** `http://127.0.0.1`.
  Com o IP a chamada morre em "Failed to fetch".
- Só as portas 9223–9232, e o próprio bridge costuma ocupar 9223 e 9224 — use
  9225 em diante.

Subir servidor local pode esbarrar na permissão da sessão. Se esbarrar, vá de
`figma_capture_screenshot`, uma tela por vez.
