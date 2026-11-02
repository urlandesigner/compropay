"""Monta o vídeo "Como favoritar um estabelecimento?".

Entrada: telas do Figma em fig/, narração gerada aqui (Kokoro, pt-BR).
Saída: out/favoritar.mp4 (1920x1080, texto na lateral) + out/favoritar.vtt

Fonte, modelo de voz e venv vêm de ../video-comum (ver o README de lá).
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
SW, SH = 430, 932                      # tela do app, 1x do Figma
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "Na tela inicial, em Favoritos, toque em Novo.",
    "Você vê os estabelecimentos mais próximos de você.",
    "Ou busque pelo nome.",
    "Toque no marcador do estabelecimento.",
    "Confirme em Favoritar.",
    "Pronto! Ele já aparece em Meus favoritos.",
]
ROTULO = "Favoritar um estabelecimento"
VOZ = os.environ.get("VOZ", "pf_dora")

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
def carregar(n): return Image.open(os.path.join(FIG, n)).convert("RGBA")

inicio_alta = carregar("01-inicio.png")              # 430x1255: tab bar fixa no rodapé
TAB = 120
INICIO = Image.new("RGBA", (SW, SH))
INICIO.paste(inicio_alta.crop((0, 0, SW, SH - TAB)), (0, 0))
INICIO.paste(inicio_alta.crop((0, 1255 - TAB, SW, 1255)), (0, SH - TAB))

FAVORITAR = carregar("02-favoritar.png")             # busca vazia + "Próximos de mim"
MARCADO = carregar("04-marcado.png")                 # resultado com o 2º item já favoritado
MEUS = carregar("05-meus-favoritos.png")
SHEET = carregar("06-sheet-sozinho.png")             # 430x288, cantos transparentes
SHEET_Y = 644                                        # topo do sheet dentro da tela

# busca digitada: o campo de "04" colado na tela "02"
CAMPO = (20, 124, 410, 176)
BUSCA_PATCH = MARCADO.crop(CAMPO)
def com_busca(a):
    im = FAVORITAR.copy()
    if a > 0:
        p = BUSCA_PATCH.copy(); p.putalpha(int(255 * a))
        im.alpha_composite(p, (CAMPO[0], CAMPO[1]))
    return im

# resultado ainda não favoritado: marcador vazio da 1ª linha sobre a 2ª
MARCA_VAZIA = MARCADO.crop((366, 275, 394, 303))
RESULTADO = MARCADO.copy()
RESULTADO.paste(MARCA_VAZIA, (366, 365))

def supersample(fn, w, h, k=3):
    big = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); fn(ImageDraw.Draw(big), k)
    return big.resize((w, h), Image.LANCZOS)

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
    """Tempos de fala e eventos, a partir da duração de cada frase."""
    T = {}; fala = []; t = 0.5
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e
    s, e = falar(0); T["tap1"] = e + 0.15; T["tr1"] = T["tap1"] + 0.25
    t = T["tr1"] + 0.6
    s, e = falar(1)
    t = e + 0.5
    s, e = falar(2); T["tap_busca"] = s + 0.15; T["digita"] = s + 0.5
    T["tr2"] = max(e + 0.2, T["digita"] + 0.7)
    t = T["tr2"] + 0.6
    s, e = falar(3); T["tap_marca"] = e + 0.15; T["sheet_up"] = T["tap_marca"] + 0.2
    t = T["sheet_up"] + 0.75
    s, e = falar(4); T["tap_ok"] = e + 0.15; T["sheet_down"] = T["tap_ok"] + 0.3
    t = T["sheet_down"] + 0.7
    s, e = falar(5); T["tr3"] = s + 0.5; T["fim"] = e + 1.6
    return fala, T

TR = 0.42   # duração da transição de tela
def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def resultado_em(t, T):
    """Tela de resultado, com o sheet por cima enquanto ele estiver no ar."""
    base = MARCADO if t >= T["sheet_down"] else RESULTADO
    im = base.copy()
    up = ease(ramp(t, T["sheet_up"], T["sheet_up"] + 0.35))
    down = ease(ramp(t, T["sheet_down"], T["sheet_down"] + 0.3))
    v = up * (1 - down)
    if v > 0:
        im.alpha_composite(Image.new("RGBA", (SW, SH), (10, 0, 30, int(120 * v))))
        im.alpha_composite(SHEET, (0, int(SH - (SH - SHEET_Y) * v)))
    return im

def busca_em(t, T):
    return com_busca(ease(ramp(t, T["digita"], T["digita"] + 0.3)))

def tela_em(t, T):
    if t < T["tr1"]: return INICIO
    if t < T["tr1"] + TR: return slide(INICIO, FAVORITAR, (t - T["tr1"]) / TR)
    if t < T["tr2"]: return busca_em(t, T)
    if t < T["tr2"] + TR: return slide(busca_em(t, T), resultado_em(t, T), (t - T["tr2"]) / TR)
    if t < T["tr3"]: return resultado_em(t, T)
    if t < T["tr3"] + TR: return slide(resultado_em(t, T), MEUS, (t - T["tr3"]) / TR)
    return MEUS

def toques(T):
    return [(T["tap1"], 52, 551),                       # "+ Novo" em Favoritos
            (T["tap_busca"], 215, 150),                 # campo de busca
            (T["tap_marca"], 380, 379),                 # marcador do 2º item
            (T["tap_ok"], 315, 884)]                    # botão "Favoritar" do sheet

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
    """Índice da frase visível e opacidade (troca suave entre frases)."""
    i = 0
    for k, (s, e) in enumerate(fala):
        if t >= s - 0.25: i = k
    s = fala[i][0]
    return i, ease(ramp(t, s - 0.25, s + 0.05))

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
    open(os.path.join(OUT, "favoritar.vtt"), "w").write(vtt(fala))

    mp4 = os.path.join(OUT, "favoritar.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    lista = toques(T); n = int(total * FPS)
    poster_f = int((T["sheet_up"] + 0.5) * FPS)
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, T).copy()
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
        if f == poster_f: rgb.save(os.path.join(OUT, "favoritar.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for k, v in sorted(T.items(), key=lambda kv: kv[1]): print(f"  {k}: {v:.2f}")

if __name__ == "__main__":
    main()
