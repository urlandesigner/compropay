"""Prepara as telas reais da abertura do vídeo do cadastro.

Lê as capturas do iPhone em capturas-iphone/cadastro/ (fora do Git: trazem o CPF digitado),
borra o CPF e grava em fig/ no tamanho do aparelho do Figma (414x896), pronto para o build.py.

    ../video-comum/.venv/bin/python preparar-telas-reais.py

Cada linha de TELAS diz: arquivo de saída, captura de origem e as caixas (x0, y0, x1, y1, na
captura em 702x1526) que escondem o CPF. O borrão é um mosaico seguido de desfoque: não dá para
ler nem recuperar o número. Na tela com o CPF digitado, a barra de status (hora e bateria) vem da
tela anterior, para o relógio não andar para trás na transição.
"""
import os
from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
CAP = os.environ.get("CAPTURAS_DIR") or os.path.join(AQUI, "..", "capturas-iphone", "cadastro")
FIG = os.path.join(AQUI, "fig")
SW, SH = 414, 896
BARRA = 105                                    # altura da barra de status na captura (px)

# saída em fig/       captura de origem     caixas do CPF          barra de status vinda de
TELAS = [
    ("01-entrada-vazia", "11-entrada-vazia.png", [],                      None),
    ("02-entrada-cpf",   "01-tela.png",          [(28, 1180, 290, 1232)], "11-entrada-vazia.png"),
]

def borrar(im, caixa):
    x0, y0, x1, y1 = caixa
    trecho = im.crop(caixa)
    w, h = trecho.size
    mosaico = trecho.resize((max(w // 14, 1), max(h // 14, 1)), Image.BILINEAR).resize((w, h), Image.NEAREST)
    im.paste(mosaico.filter(ImageFilter.GaussianBlur(5)), (x0, y0))

def main():
    for saida, origem, caixas, barra in TELAS:
        im = Image.open(os.path.join(CAP, origem)).convert("RGBA")
        for c in caixas: borrar(im, c)
        if barra:
            b = Image.open(os.path.join(CAP, barra)).convert("RGBA")
            im.paste(b.crop((0, 0, im.size[0], BARRA)), (0, 0))
        im.resize((SW, SH), Image.LANCZOS).save(os.path.join(FIG, saida + ".png"))
        print(f"{saida}.png  <- {origem}  ({len(caixas)} borrão)")

if __name__ == "__main__":
    main()
