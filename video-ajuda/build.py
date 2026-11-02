"""Monta o vídeo "Como acessar a Central de Ajuda?".

Mistura os dois formatos: toque onde o usuário precisa tocar, holofote onde é
só pra mostrar o que a tela tem.

Entrada: telas em fig/, a home vem de ../video-home/fig/, narração aqui (Kokoro).
Saída: out/central-de-ajuda.mp4 (1920x1080) + out/central-de-ajuda.vtt
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
    "No menu de baixo do app, toque em Ajuda.",
    "A Central de Ajuda abre com tudo num lugar só.",
    "Em cima, a busca: escreva sua dúvida.",
    "Logo abaixo, a Lia, nossa atendente virtual.",
    "E os atalhos: FAQ, telefones, ouvidoria e endereços.",
    "Toque em Fale com a Lia para abrir o chat.",
    "Pronto, agora é só mandar sua mensagem.",
]
ROTULO = "Central de ajuda"
VOZ = os.environ.get("VOZ", "pf_dora")

# O que acende em cada frase. None = tela inteira, sem escurecer.
FOCO = [
    None,
    None,
    (20, 116, 410, 184),    # campo de busca
    (20, 207, 410, 355),    # banner "Fale com a Lia"
    (20, 378, 410, 678),    # FAQ, telefones, ouvidoria, endereços
    None,
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

# ---------------------------------------------------------------- telas
def carregar(p): return Image.open(p).convert("RGBA")

# a home tem 1255 de altura: barra de status em cima, menu colado no rodapé
home_alta = carregar(os.path.join(ROOT, "..", "video-home", "fig", "home.png"))
TAB = 120
INICIO = Image.new("RGBA", (SW, SH))
INICIO.paste(home_alta.crop((0, 0, SW, SH - TAB)), (0, 0))
INICIO.paste(home_alta.crop((0, 1255 - TAB, SW, 1255)), (0, SH - TAB))

AJUDA = carregar(os.path.join(FIG, "01-ajuda.png"))
CHAT = carregar(os.path.join(FIG, "02-email.png"))

def aplicar_foco(im, rect, forca):
    if rect is None or forca <= 0.01: return im
    x0, y0, x1, y1 = rect
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
    T = {}; fala = []; t = 0.6
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e
    s, e = falar(0); T["tap1"] = e + 0.15; T["tr1"] = T["tap1"] + 0.25
    t = T["tr1"] + 0.55
    for i in (1, 2, 3):
        s, e = falar(i); t = e + 0.45
    s, e = falar(4); t = e + 0.5
    s, e = falar(5); T["tap2"] = e + 0.15; T["tr2"] = T["tap2"] + 0.3
    t = T["tr2"] + 0.6
    s, e = falar(6); T["fim"] = e + 1.6
    return fala, T

TR = 0.42   # duração da transição de tela
def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def ativo(t, fala):
    i = 0
    for k, (ini, _) in enumerate(fala):
        if t >= ini - 0.40: i = k
    return i, ease(ramp(t, fala[i][0] - 0.40, fala[i][0] + 0.10))

def foco_em(t, fala):
    """Retângulo do holofote e força, interpolando entre duas frases."""
    i, p = ativo(t, fala)
    atual, antes = FOCO[i], (FOCO[i - 1] if i > 0 else None)
    if atual is None and antes is None: return None, 0.0
    if atual is None: return antes, 1 - p
    if antes is None: return atual, p
    return tuple(a + (b - a) * p for a, b in zip(antes, atual)), 1.0

def ajuda_em(t, fala):
    """A Central de Ajuda com o holofote da frase em cena."""
    im = AJUDA.copy()
    rect, forca = foco_em(t, fala)
    return aplicar_foco(im, rect, forca)

def tela_em(t, T, fala):
    if t < T["tr1"]: return INICIO
    if t < T["tr1"] + TR: return slide(INICIO, ajuda_em(t, fala), (t - T["tr1"]) / TR)
    if t < T["tr2"]: return ajuda_em(t, fala)
    if t < T["tr2"] + TR: return slide(ajuda_em(t, fala), CHAT, (t - T["tr2"]) / TR)
    return CHAT

def toques(T):
    return [(T["tap1"], 368, 878),      # "Ajuda", último item do menu de baixo
            (T["tap2"], 215, 285)]      # banner "Fale com a Lia"

def desenhar_toques(im, t, lista):
    d = ImageDraw.Draw(im, "RGBA")
    for t0, x, y in lista:
        if t0 - 0.35 <= t < t0:
            a = ease(ramp(t, t0 - 0.35, t0 - 0.1)); r = 26 + 8 * (1 - a)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(110 * a)), outline=ROXO + (int(230 * a),), width=3)
        elif t0 <= t < t0 + 0.5:
            p = (t - t0) / 0.5; r = 22 + 40 * ease(p)
            d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=ROXO + (int(120 * (1 - p)),))
            d.ellipse((x - r, y - r, x + r, y + r), outline=ROXO + (int(200 * (1 - p)),), width=3)

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
    clips, sr = narrar()
    dur = [len(c) / sr for c in clips]
    fala, T = montar_timeline(dur)
    total = T["fim"]
    audio = np.zeros(int((total + 0.5) * sr), dtype=np.float32)
    for (s, _), c in zip(fala, clips):
        i = int(s * sr); audio[i:i + len(c)] += c
    wav = os.path.join(OUT, "narracao.wav"); sf.write(wav, audio, sr)
    open(os.path.join(OUT, "central-de-ajuda.vtt"), "w").write(vtt(fala))

    mp4 = os.path.join(OUT, "central-de-ajuda.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    lista = toques(T); n = int(total * FPS)
    poster_f = int((fala[3][0] + 0.8) * FPS)       # banner da Lia aceso
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, T, fala).copy()
        desenhar_toques(tela, t, lista)
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
        if f == poster_f: rgb.save(os.path.join(OUT, "central-de-ajuda.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for i, (ini, fim) in enumerate(fala):
        print(f"  {i+1}. {ini:5.2f}–{fim:5.2f}  {LINHAS[i][:48]}")
    for k, v in sorted(T.items(), key=lambda kv: kv[1]): print(f"     {k}: {v:.2f}")

if __name__ == "__main__":
    main()
