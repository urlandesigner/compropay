"""Monta o vídeo "Como criar sua conta no app ComproPay?".

Da tela de entrada até o pré-cadastro aprovado. As duas primeiras telas (entrada vazia e com o
CPF digitado) são capturas reais do app no iPhone, com o CPF borrado (ver
preparar-telas-reais.py); as demais vêm do Figma. Cada tela entra como está, em 414x896, sem
redimensionar. As três telas de 414x1091 (formulário e confirmação) rolam: o
cabeçalho e o botão ficam fixos e o meio anda.

Entrada: telas em fig/, narração gerada aqui (Kokoro, pt-BR).
Saída: out/cadastro.mp4 (1920x1080, texto na lateral) + out/cadastro.vtt
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
SW, SH = 414, 896                      # tela do app, 1x do Figma
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "Abra o app e digite o seu CPF ou CNPJ.",
    "Toque em Começar.",
    "Preencha nome, celular, e-mail, nascimento e apelido.",
    "Escolha o gênero e toque em Continuar.",
    "Confira os dados e toque em Confirmar.",
    "Agora informe o seu e-mail e toque em Continuar.",
    "Digite o código que chegou no seu e-mail.",
    "Depois, digite o código que chegou por SMS.",
    "Crie uma senha de seis números e confirme.",
    "O app abre a câmera para confirmar que é você.",
    "Centralize o rosto na marcação.",
    "Pronto! Seu pré-cadastro foi aprovado. Bem-vindo ao ComproPay!",
]
ROTULO = "Criar conta"
VOZ = os.environ.get("VOZ", "pf_dora")

def narrar():
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(COMUM, "tts/kokoro-v1.0.onnx"), os.path.join(COMUM, "tts/voices-v1.0.bin"))
    clips = []
    for txt in LINHAS:
        s, sr = k.create(txt, voice=VOZ, speed=1.0, lang="pt-br")
        idx = np.where(np.abs(s) > 0.01)[0]
        s = s[max(idx[0] - 600, 0): idx[-1] + 1200]
        clips.append(s)
    return clips, sr

# ---------------------------------------------------------------- telas
ARQ = {
    "01": "01-entrada-vazia", "02": "02-entrada-cpf",        # telas reais do iPhone (preparar-telas-reais.py)
    "04": "04-form-vazio", "05": "05-form-preenchido", "06": "06-confirme",
    "07": "07-email-vazio", "08": "08-email-digitado",
    "09": "09-email-codigo-vazio", "10": "10-email-codigo",
    "11": "11-sms-vazio", "12": "12-sms-codigo",
    "13": "13-senha-vazia", "14": "14-senha-preenchida",
    "15": "15-ambiente-seguro", "16": "16-liveness", "17": "17-processando",
    "18": "18-pre-cadastro",
}
IMG = {k: Image.open(os.path.join(FIG, v + ".png")).convert("RGBA") for k, v in ARQ.items()}

# Telas mais altas que o aparelho: grupo de rolagem e altura do trecho fixo no rodapé.
TOPO = 100
ALTAS = {"04": ("form", 90), "05": ("form", 90), "06": ("conf", 130)}
ROLAGEM_MAX = {"form": 195, "conf": 195}

def alta(key, s):
    """A tela de 1091 de altura vista por uma janela de 896, rolada s pixels."""
    _, fixo = ALTAS[key]
    im = IMG[key]; h = im.size[1]
    janela = SH - TOPO - fixo
    out = Image.new("RGBA", (SW, SH), (245, 245, 245, 255))
    out.paste(im.crop((0, 0, SW, TOPO)), (0, 0))
    topo = int(round(TOPO + s))
    out.paste(im.crop((0, topo, SW, topo + janela)), (0, TOPO))
    out.paste(im.crop((0, h - fixo, SW, h)), (0, SH - fixo))
    return out

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

TR, FD = 0.42, 0.30      # duração do deslize entre telas e da troca de estado
RIP = 0.30               # duração do círculo do toque: acaba antes do deslize começar

def montar_timeline(dur):
    """Fala, e os eventos de tela (deslize, troca, rolagem, toque) a partir dela."""
    EV = []; fala = []; t = 0.6
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e
    def tap(ts, x, y): EV.append(dict(t=ts, tipo="tap", x=x, y=y))
    def desliza(ts, k): EV.append(dict(t=ts, tipo="desliza", k=k))
    def troca(ts, k): EV.append(dict(t=ts, tipo="troca", k=k))
    def rola(ts, g, para, d): EV.append(dict(t=ts, tipo="rola", g=g, para=para, d=d))
    CTA = (207, 836)       # botão de baixo das telas de 896

    s, e = falar(0); tap(s + 0.20, 150, 712); troca(s + 0.80, "02"); t = e + 0.5
    s, e = falar(1); tap(e + 0.15, 207, 799); desliza(e + 0.45, "04"); t = e + 1.1
    s, e = falar(2); troca(s + 0.6, "05"); t = e + 0.5
    s, e = falar(3); rola(s + 0.1, "form", 195, 0.9)
    tap(e + 0.15, *CTA); desliza(e + 0.45, "06"); t = e + 1.1
    s, e = falar(4); rola(s + 0.4, "conf", 195, 1.6)
    tap(e + 0.15, 207, 796); desliza(e + 0.45, "07"); t = e + 1.1
    s, e = falar(5); troca(s + 1.0, "08")
    tap(e + 0.15, *CTA); desliza(e + 0.45, "09"); t = e + 1.1
    s, e = falar(6); troca(s + 1.3, "10")
    tap(e + 0.50, *CTA); desliza(e + 0.80, "11"); t = e + 1.45
    s, e = falar(7); troca(s + 1.5, "12")
    tap(e + 0.50, *CTA); desliza(e + 0.80, "13"); t = e + 1.45
    s, e = falar(8); troca(s + 1.0, "14")
    tap(e + 0.15, *CTA); desliza(e + 0.45, "15"); t = e + 1.1
    s, e = falar(9); desliza(e + 0.7, "16"); t = e + 1.5
    s, e = falar(10); troca(e + 0.5, "17"); desliza(e + 1.9, "18"); t = e + 2.6
    s, e = falar(11)
    return fala, EV, e + 1.9

def rolagem(g, t, EV):
    base = 0.0
    for ev in sorted((x for x in EV if x["tipo"] == "rola" and x["g"] == g), key=lambda x: x["t"]):
        if t < ev["t"]: break
        p = ease(ramp(t, ev["t"], ev["t"] + ev["d"]))
        if p < 1: return base + (ev["para"] - base) * p
        base = ev["para"]
    return base

def quadro_da_tela(key, t, EV):
    if key in ALTAS: return alta(key, rolagem(ALTAS[key][0], t, EV))
    return IMG[key]

def desliza_img(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def tela_em(t, EV):
    trans = sorted((x for x in EV if x["tipo"] in ("desliza", "troca")), key=lambda x: x["t"])
    cur = "01"
    for ev in trans:
        if t < ev["t"]: break
        dur = TR if ev["tipo"] == "desliza" else FD
        if t < ev["t"] + dur:
            p = (t - ev["t"]) / dur
            a, b = quadro_da_tela(cur, t, EV), quadro_da_tela(ev["k"], t, EV)
            return desliza_img(a, b, p) if ev["tipo"] == "desliza" else Image.blend(a, b, ease(p))
        cur = ev["k"]
    return quadro_da_tela(cur, t, EV)

def desenhar_toques(im, t, EV):
    d = ImageDraw.Draw(im, "RGBA")
    for ev in EV:
        if ev["tipo"] != "tap": continue
        t0, x, y = ev["t"], ev["x"], ev["y"]
        if t0 - 0.35 <= t < t0:
            a = ease(ramp(t, t0 - 0.35, t0 - 0.1)); r = 26 + 8 * (1 - a)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(110 * a)), outline=ROXO + (int(230 * a),), width=3)
        elif t0 <= t < t0 + RIP:
            p = (t - t0) / RIP; r = 22 + 40 * ease(p)
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
    fala, EV, total = montar_timeline(dur)
    audio = np.zeros(int((total + 0.5) * sr), dtype=np.float32)
    for (s, _), c in zip(fala, clips):
        i = int(s * sr); audio[i:i + len(c)] += c
    wav = os.path.join(OUT, "narracao.wav"); sf.write(wav, audio, sr)
    open(os.path.join(OUT, "cadastro.vtt"), "w").write(vtt(fala))

    mp4 = os.path.join(OUT, "cadastro.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    n = int(total * FPS)
    poster_f = int((fala[2][0] + 2.5) * FPS)        # formulário preenchido
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, EV).copy()
        desenhar_toques(tela, t, EV)
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
        if f == poster_f: rgb.save(os.path.join(OUT, "cadastro.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for i, (ini, fim) in enumerate(fala):
        print(f"  {i+1:2}. {ini:5.2f}–{fim:5.2f}  {LINHAS[i][:52]}")

if __name__ == "__main__":
    main()
