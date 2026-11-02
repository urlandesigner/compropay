"""Monta o vídeo "A tela inicial".

Não é passo a passo: é um tour. Ninguém toca em nada. A tela rola e cada seção
acende enquanto o resto escurece.

Entrada: fig/home.png (frame 430x1255 do Figma), narração gerada aqui (Kokoro).
Saída: out/home.mp4 (1920x1080, texto na lateral) + out/home.vtt
"""
import os, subprocess, sys
import numpy as np
import soundfile as sf
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
COMUM = os.path.join(ROOT, "..", "video-comum")
FIG = os.path.join(ROOT, "fig")
OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
FPS, W, H = 30, 1920, 1080
SW, SH = 430, 932                      # tela do app, 1x do Figma
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "No topo, seu perfil, os atalhos rápidos e os avisos.",
    "Logo abaixo, seus cartões, cada um com o saldo à vista.",
    "O saldo da carteira, com transferir, depositar e cobrar na mão.",
    "Os estabelecimentos que você favoritou, e o atalho pra adicionar outros.",
    "As ofertas e vantagens do momento.",
    "E os atalhos dos serviços: rede, cashback, rotativo, boletos e o resto.",
    "No rodapé, o menu: Início, Extrato, Pagar, Cartões e Ajuda.",
    "Essa é a tela inicial do ComproPay.",
]
ROTULO = "A tela inicial"
VOZ = os.environ.get("VOZ", "pf_dora")

# Quanto a tela está rolada em cada frase, e que pedaço acende.
# Os limites são medidos no frame de 1255 de altura; "fixo" é o menu inferior,
# que não rola. A última frase não acende nada: a tela inteira reaparece.
ROLAGEM = [0, 0, 0, 0, 80, 340, 340, 0]
FOCO = [
    ("rola", 56, 128),      # header
    ("rola", 118, 312),     # meus cartões
    ("rola", 322, 472),     # saldo na carteira
    ("rola", 481, 612),     # favoritos
    ("rola", 632, 835),     # vantagens para você
    ("rola", 848, 1136),    # serviços
    ("fixo", 0, 0),         # menu inferior
    None,
]

def narrar():
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(COMUM, "tts/kokoro-v1.0.onnx"), os.path.join(COMUM, "tts/voices-v1.0.bin"))
    clips = []
    for txt in LINHAS:
        s, sr = k.create(txt, voice=VOZ, speed=1.0, lang="pt-br")
        # corta silêncio das pontas
        idx = np.where(np.abs(s) > 0.01)[0]
        s = s[max(idx[0] - 600, 0): idx[-1] + 1200]
        clips.append(s)
    return clips, sr

# ---------------------------------------------------------------- tela
HOME = Image.open(os.path.join(FIG, "home.png")).convert("RGBA")
ALTA = HOME.size[1]                    # 1255
TOPO = 62                              # barra de status, não rola
TAB = 120                              # faixa do menu inferior, não rola
VISTA = SH - TOPO - TAB                # 750: altura da parte que rola
FIM_CONTEUDO = 1152                    # fim dos serviços (1128) mais a folga de baixo
ROLAGEM_MAX = FIM_CONTEUDO - TOPO - VISTA

BARRA = HOME.crop((0, 0, SW, TOPO))
MENU = HOME.crop((0, ALTA - TAB, SW, ALTA))
# o menu inferior, dentro da tela do vídeo, ocupa de SH-TAB a SH
MENU_RECT = (14.0, SH - TAB + 14.0, 416.0, SH - 9.0)

def tela_em(s):
    """A tela do aparelho com o conteúdo rolado em s pixels."""
    im = Image.new("RGBA", (SW, SH), "white")
    im.paste(BARRA, (0, 0))
    topo = int(round(TOPO + s))
    im.paste(HOME.crop((0, topo, SW, topo + VISTA)), (0, TOPO))
    im.paste(MENU, (0, SH - TAB))
    return im

def retangulo(spec, s):
    """Onde o holofote fica, na tela do aparelho, para uma dada rolagem."""
    if spec is None: return None
    modo, a, b = spec
    if modo == "fixo": return MENU_RECT
    y0 = TOPO + (a - TOPO - s); y1 = TOPO + (b - TOPO - s)
    return (14.0, max(y0, TOPO - 6), 416.0, min(y1, SH - TAB - 6))

def aplicar_foco(im, rect, forca):
    if rect is None or forca <= 0.01: return im
    x0, y0, x1, y1 = rect
    if y1 - y0 < 8: return im
    sombra = Image.new("L", (SW, SH), int(170 * forca))
    ImageDraw.Draw(sombra).rounded_rectangle((x0, y0, x1, y1), 18, fill=0)
    capa = Image.new("RGBA", (SW, SH), (16, 5, 38, 255)); capa.putalpha(sombra)
    im.alpha_composite(capa)
    ImageDraw.Draw(im, "RGBA").rounded_rectangle(
        (x0, y0, x1, y1), 18, outline=(178, 126, 248, int(215 * forca)), width=3)
    return im

# ---------------------------------------------------------------- aparelho
BEZEL, R_TELA = 12, 50
PW, PH = SW + 2 * BEZEL, SH + 2 * BEZEL
PX, PY = 380, (H - PH) // 2
mask_tela = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(mask_tela).rounded_rectangle((0, 0, SW - 1, SH - 1), R_TELA, fill=255)

def fundo():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    c1, c2 = np.array([247, 243, 253]), np.array([234, 224, 250])
    t = np.clip(0.6 * x + 0.4 * y, 0, 1)[..., None]
    bg = Image.fromarray((c1 * (1 - t) + c2 * t).astype(np.uint8), "RGB").convert("RGBA")
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((PX + 10, PY + 30, PX + PW + 10, PY + PH + 30), R_TELA + BEZEL, fill=(60, 20, 110, 70))
    bg.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(28)))
    ImageDraw.Draw(bg).rounded_rectangle((PX, PY, PX + PW, PY + PH), R_TELA + BEZEL, fill=(22, 18, 30))
    return bg
FUNDO = fundo()

# ---------------------------------------------------------------- texto lateral
TX, TW = 1000, 780
def bloco_texto(i):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font("SemiBold", 60); palavras = LINHAS[i].split(); linhas, cur = [], ""
    for p in palavras:
        tentativa = (cur + " " + p).strip()
        if d.textlength(tentativa, font=f) > TW and cur: linhas.append(cur); cur = p
        else: cur = tentativa
    linhas.append(cur)
    alt = len(linhas) * 78
    y0 = H // 2 - alt // 2 + 20
    d.text((TX, y0 - 70), ROTULO.upper(), font=font("SemiBold", 22), fill=ROXO)
    for j, l in enumerate(linhas): d.text((TX, y0 + j * 78), l, font=f, fill=TINTA)
    return im
TEXTOS = [bloco_texto(i) for i in range(len(LINHAS))]

# ---------------------------------------------------------------- animação
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

def montar_timeline(dur):
    """Uma frase atrás da outra, com uma respirada entre elas."""
    fala = []; t = 0.7
    for d in dur:
        fala.append((t, t + d)); t += d + 0.5
    return fala, t + 1.1

def ativo(t, fala):
    """Frase em cena e o quanto a transição para ela já andou."""
    i = 0
    for k, (ini, _) in enumerate(fala):
        if t >= ini - 0.45: i = k
    return i, ease(ramp(t, fala[i][0] - 0.45, fala[i][0] + 0.10))

def scroll_em(t, fala):
    i, p = ativo(t, fala)
    a = ROLAGEM[i - 1] if i > 0 else ROLAGEM[0]
    return a + (ROLAGEM[i] - a) * p

def foco_em(t, fala, s):
    """Retângulo do holofote e sua força, interpolando entre duas seções."""
    i, p = ativo(t, fala)
    atual = retangulo(FOCO[i], s)
    antes = retangulo(FOCO[i - 1], s) if i > 0 else None
    if atual is None and antes is None: return None, 0.0
    if atual is None: return antes, 1 - p
    if antes is None: return atual, p
    return tuple(a + (b - a) * p for a, b in zip(antes, atual)), 1.0

def texto_em(t, fala):
    i = 0
    for k, (ini, _) in enumerate(fala):
        if t >= ini - 0.25: i = k
    return i, ease(ramp(t, fala[i][0] - 0.25, fala[i][0] + 0.05))

def vtt(fala):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
    out = ["WEBVTT", ""]
    for i, (s, e) in enumerate(fala):
        fim = fala[i + 1][0] - 0.05 if i + 1 < len(fala) else e + 1.2
        out.append(f"{i+1}\n{ts(s)} --> {ts(fim)}\n{LINHAS[i]}\n")
    return "\n".join(out)

def main():
    assert ROLAGEM_MAX >= max(ROLAGEM), f"rolagem passa do fim do conteúdo ({ROLAGEM_MAX})"
    clips, sr = narrar()
    dur = [len(c) / sr for c in clips]
    fala, total = montar_timeline(dur)
    audio = np.zeros(int((total + 0.5) * sr), dtype=np.float32)
    for (s, _), c in zip(fala, clips):
        i = int(s * sr); audio[i:i + len(c)] += c
    wav = os.path.join(OUT, "narracao.wav"); sf.write(wav, audio, sr)
    open(os.path.join(OUT, "home.vtt"), "w").write(vtt(fala))

    mp4 = os.path.join(OUT, "home.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    n = int(total * FPS)
    poster_f = int((fala[1][0] + 0.7) * FPS)      # cartões acesos
    for f in range(n):
        t = f / FPS
        s = scroll_em(t, fala)
        tela = tela_em(s)
        rect, forca = foco_em(t, fala, s)
        aplicar_foco(tela, rect, forca)
        quadro = FUNDO.copy()
        quadro.paste(tela, (PX + BEZEL, PY + BEZEL), mask_tela)
        i, a = texto_em(t, fala)
        if a < 1 and i > 0:
            prev = TEXTOS[i - 1].copy(); prev.putalpha(prev.getchannel("A").point(lambda v: int(v * (1 - a))))
            quadro.alpha_composite(prev)
        cur = TEXTOS[i] if a >= 1 else TEXTOS[i].copy()
        if a < 1: cur.putalpha(cur.getchannel("A").point(lambda v: int(v * a)))
        quadro.alpha_composite(cur)
        fo = ramp(t, total - 0.5, total)
        if fo > 0: quadro.alpha_composite(Image.new("RGBA", (W, H), (247, 243, 253, int(255 * fo))))
        rgb = quadro.convert("RGB")
        ff.stdin.write(rgb.tobytes())
        if f == poster_f: rgb.save(os.path.join(OUT, "home.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for i, (ini, fim) in enumerate(fala):
        print(f"  {i+1}. {ini:5.2f}–{fim:5.2f}  rolagem {ROLAGEM[i]:3}  {LINHAS[i][:46]}")

if __name__ == "__main__":
    main()
