"""Monta o vídeo "Como consultar o saldo de seus Cartões Comprocard?".

Entrada: telas do Figma em fig/, narração gerada aqui (Kokoro, pt-BR).
Saída: out/saldo.mp4 (1920x1080, texto na lateral) + out/saldo.vtt

Fonte, modelo de voz e venv vêm de ../video-comum (ver o README de lá).

Atenção: as telas da seção "Cartão" têm 896 de altura, não 932 como as de
"Favoritar" e "Extrato". SH acompanha, e o recorte da tela inicial também.
"""
import os, subprocess, sys
import numpy as np
import soundfile as sf
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
COMUM = os.path.join(ROOT, '..', 'video-comum')
FIG = os.path.join(ROOT, "fig")
OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
FPS, W, H = 30, 1920, 1080
SW, SH = 430, 896                      # tela do app, 1x do Figma
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "Na tela inicial, toque em Cartões, na barra de baixo.",
    "O saldo de cada cartão aparece direto nele.",
    "Você também vê qual é o principal e se algum está bloqueado. Pronto!",
]
ROTULO = "Saldo dos cartões"
VOZ = os.environ.get("VOZ", "pf_dora")

def narrar():
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(COMUM, "tts/kokoro-v1.0.onnx"), os.path.join(COMUM, "tts/voices-v1.0.bin"))
    clips = []
    for txt in LINHAS:
        s, sr = k.create(txt, voice=VOZ, speed=1.0, lang="pt-br")
        idx = np.where(np.abs(s) > 0.01)[0]          # corta silêncio das pontas
        clips.append(s[max(idx[0] - 600, 0): idx[-1] + 1200])
    return clips, sr

# ---------------------------------------------------------------- telas
def carregar(n): return Image.open(os.path.join(FIG, n)).convert("RGBA")

inicio_alta = carregar("00-inicio.png")              # 430x1255: tab bar fixa no rodapé
TAB = 120
INICIO = Image.new("RGBA", (SW, SH))
INICIO.paste(inicio_alta.crop((0, 0, SW, SH - TAB)), (0, 0))
INICIO.paste(inicio_alta.crop((0, 1255 - TAB, SW, 1255)), (0, SH - TAB))

CARTOES = carregar("01-cartoes.png")

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
    y0 = H // 2 - (len(linhas) * 78) // 2 + 20
    d.text((TX, y0 - 70), ROTULO.upper(), font=font("SemiBold", 22), fill=ROXO)
    for j, l in enumerate(linhas): d.text((TX, y0 + j * 78), l, font=f, fill=TINTA)
    return im
TEXTOS = [bloco_texto(i) for i in range(len(LINHAS))]

# ---------------------------------------------------------------- animação
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

def montar_timeline(dur):
    T = {}; fala = []; t = 0.5
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e
    s, e = falar(0); T["tap1"] = e + 0.15; T["tr1"] = T["tap1"] + 0.25
    t = T["tr1"] + 0.6
    s, e = falar(1); T["saldo1"] = s + 0.25; T["saldo2"] = s + 0.95
    t = max(e, T["saldo2"] + 1.1) + 0.45
    s, e = falar(2); T["selo1"] = s + 0.3; T["selo2"] = s + 1.0
    T["fim"] = max(e, T["selo2"] + 1.1) + 1.3
    return fala, T

TR = 0.42   # duração da transição de tela
def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def tela_em(t, T):
    if t < T["tr1"]: return INICIO
    if t < T["tr1"] + TR: return slide(INICIO, CARTOES, (t - T["tr1"]) / TR)
    return CARTOES

def toques(T):
    # "Cartões" da barra: y vem da faixa 1135..1255 do PNG alto, colada em SH-TAB
    return [(T["tap1"], 292, SH - TAB + (1201 - (1255 - TAB)))]

# Destaques: nada é tocado aqui, a informação já está na tela. Um contorno
# acende em volta do que a narração cita, em vez de fingir um toque.
def destaques(T):
    return [(T["saldo1"], (26, 340, 154, 394)),       # R$300,00 do primeiro cartão
            (T["saldo2"], (26, 555, 154, 609)),       # R$200,00 do segundo
            (T["selo1"], (318, 344, 404, 374)),       # selo "Principal"
            (T["selo2"], (306, 557, 404, 587))]       # selo "Bloqueado" (o número do
                                                      # cartão vem logo abaixo: não sobrar)

DUR_DESTAQUE = 2.0
def desenhar_destaques(im, t, lista):
    """Contorno que acende em volta do que a narração cita.

    Desenhado numa camada transparente e composto por cima: ImageDraw com
    fill translúcido sobre a própria tela saía opaco e tapava o saldo.
    Sem preenchimento, de propósito — os cartões são coloridos e qualquer
    véu por cima suja a cor.
    """
    camada = None
    for t0, (x0, y0, x1, y1) in lista:
        if not (t0 <= t < t0 + DUR_DESTAQUE): continue
        entra = ease(ramp(t, t0, t0 + 0.25))
        sai = ease(ramp(t, t0 + DUR_DESTAQUE - 0.4, t0 + DUR_DESTAQUE))
        a = entra * (1 - sai)
        if a <= 0: continue
        if camada is None:
            camada = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
            dc = ImageDraw.Draw(camada)
        folga = 10 * (1 - entra)
        dc.rounded_rectangle((x0 - folga, y0 - folga, x1 + folga, y1 + folga), 12,
                             outline=ROXO + (int(235 * a),), width=3)
    if camada is not None:
        im.alpha_composite(camada)

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
    for k, (s, e) in enumerate(fala):
        if t >= s - 0.25: i = k
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
    open(os.path.join(OUT, "saldo.vtt"), "w").write(vtt(fala))

    mp4 = os.path.join(OUT, "saldo.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    toqs, dests = toques(T), destaques(T)
    n = int(total * FPS)
    poster_f = int((T["saldo1"] + 0.6) * FPS)        # pôster com o saldo aceso
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, T).copy()
        desenhar_toques(tela, t, toqs)
        if t >= T["tr1"] + TR: desenhar_destaques(tela, t, dests)
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
        if f == poster_f: rgb.save(os.path.join(OUT, "saldo.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for k, v in sorted(T.items(), key=lambda kv: kv[1]): print(f"  {k}: {v:.2f}")

if __name__ == "__main__":
    main()
