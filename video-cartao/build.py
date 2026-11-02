"""Monta o vídeo "Como cadastrar um Cartão Comprocard?".

Entrada: telas do Figma em fig/, narração gerada aqui (Kokoro, pt-BR).
Saída: out/cadastrar-cartao.mp4 (1920x1080, texto na lateral) + out/cadastrar-cartao.vtt
"""
import os, subprocess, sys
import numpy as np
import soundfile as sf
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "fig")
OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
COMUM = os.path.join(ROOT, "..", "video-comum")
FPS, W, H = 30, 1920, 1080
SW, SH = 430, 896                      # tela do app, 1x do Figma
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "Na aba Cartões, toque em Adicionar cartão.",
    "Informe o número do cartão.",
    "Depois o nome do titular, o vencimento e o CVV.",
    "Marque se esse é o seu cartão principal.",
    "Escolha a arte do cartão.",
    "Vale escolher a mesma do cartão físico.",
    "Confira e toque em Salvar.",
    "Pronto! O cartão já está na sua carteira.",
]
ROTULO = "Cadastrar um cartão"
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
def padronizar(im):
    """As duas telas do formulário saíram do Figma com 414 de largura, não 430.

    Em vez de esticar a tela (o que deformaria o texto), completa a diferença
    repetindo a coluna de cada borda — que é do mesmo cinza de fundo, então a
    emenda não aparece.
    """
    if im.width == SW: return im
    falta = SW - im.width; esq = falta // 2; dire = falta - esq
    novo = Image.new("RGBA", (SW, SH))
    novo.paste(im, (esq, 0))
    novo.paste(im.crop((0, 0, 1, SH)).resize((esq, SH)), (0, 0))
    novo.paste(im.crop((im.width - 1, 0, im.width, SH)).resize((dire, SH)), (esq + im.width, 0))
    return novo

def carregar(n): return padronizar(Image.open(os.path.join(FIG, n)).convert("RGBA"))

CARTOES = carregar("06-cartoes.png")
VAZIO   = carregar("01-form-vazio.png")
CHEIO   = carregar("02-form-preenchido.png")
ARTE0   = carregar("03-arte-nenhuma.png")
ARTE1   = carregar("04-arte-escolhida.png")
PRONTO  = carregar("05-pronto.png")

DX = (SW - 414) // 2                   # deslocamento das telas de 414 já centradas

# Faixas de pixel em que o formulário vazio vira preenchido. Vêm da diferença
# entre as duas telas: cada campo mexe em duas alturas, a prévia do cartão lá
# em cima e o campo em si mais abaixo.
BANDAS = [
    ("rev_num",   [(225, 252), (444, 520)]),
    ("rev_nome",  [(292, 320), (534, 610)]),
    ("rev_venc",  [(624, 700)]),
    ("rev_check", [(740, 772)]),
]

def form_em(t, T):
    im = VAZIO.copy()
    for chave, faixas in BANDAS:
        a = ease(ramp(t, T[chave], T[chave] + 0.28))
        if a <= 0: continue
        for y0, y1 in faixas:
            p = CHEIO.crop((0, y0, SW, y1))
            if a < 1: p = p.copy(); p.putalpha(int(255 * a))
            im.alpha_composite(p, (0, y0))
    return im

CARTAO_NOVO = (20, 204, 410, 403)      # o cartão de cima na lista de Cartões

def destaque_cartao(im, t, T):
    """Põe um aro em volta do cartão recém-cadastrado, no fim do vídeo.

    A tela de Cartões abre e fecha o vídeo igualzinha — o Figma não tem uma
    versão dela sem o cartão novo. Sem o aro, a última frase diz que o cartão
    entrou na carteira e a tela não mostra nada tendo mudado.
    """
    ini = T["tr4"] + TR
    a = ease(ramp(t, ini, ini + 0.4)) * (1 - ramp(t, T["fim"] - 1.0, T["fim"] - 0.4))
    if a <= 0: return
    x0, y0, x1, y1 = CARTAO_NOVO
    aro = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(aro)
    d.rounded_rectangle((x0 - 9, y0 - 9, x1 + 9, y1 + 9), 26, outline=ROXO + (int(90 * a),), width=10)
    d.rounded_rectangle((x0 - 7, y0 - 7, x1 + 7, y1 + 7), 24, outline=ROXO + (int(235 * a),), width=4)
    im.alpha_composite(aro)

def arte_em(t, T):
    a = ease(ramp(t, T["marca_arte"], T["marca_arte"] + 0.25))
    if a <= 0: return ARTE0
    if a >= 1: return ARTE1
    im = ARTE0.copy(); p = ARTE1.copy(); p.putalpha(int(255 * a)); im.alpha_composite(p)
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

# ---------------------------------------------------------------- animação
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

def montar_timeline(dur):
    """Tempos de fala e eventos, a partir da duração de cada frase."""
    T = {}; fala = []; t = 0.5
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e

    s, e = falar(0); T["tap_add"] = e + 0.15; T["tr1"] = T["tap_add"] + 0.25
    t = T["tr1"] + 0.6

    s, e = falar(1); T["tap_num"] = s + 0.15; T["rev_num"] = s + 0.5
    t = max(e, T["rev_num"] + 0.3) + 0.35

    s, e = falar(2); T["rev_nome"] = s + 0.35; T["rev_venc"] = T["rev_nome"] + 0.65
    t = max(e, T["rev_venc"] + 0.3) + 0.35

    s, e = falar(3); T["tap_check"] = s + 0.2; T["rev_check"] = T["tap_check"] + 0.12
    T["tap_cont1"] = max(e + 0.2, T["rev_check"] + 0.5); T["tr2"] = T["tap_cont1"] + 0.25
    t = T["tr2"] + 0.6

    s, e = falar(4); T["tap_arte"] = e + 0.1; T["marca_arte"] = T["tap_arte"] + 0.12
    t = T["marca_arte"] + 0.55

    s, e = falar(5); T["tap_cont2"] = e + 0.15; T["tr3"] = T["tap_cont2"] + 0.25
    t = T["tr3"] + 0.6

    s, e = falar(6); T["tap_salvar"] = e + 0.15; T["tr4"] = T["tap_salvar"] + 0.25
    t = T["tr4"] + 0.6

    s, e = falar(7); T["fim"] = e + 1.6
    return fala, T

TR = 0.42   # duração da transição de tela
def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def tela_em(t, T):
    if t < T["tr1"]: return CARTOES
    if t < T["tr1"] + TR: return slide(CARTOES, form_em(t, T), (t - T["tr1"]) / TR)
    if t < T["tr2"]: return form_em(t, T)
    if t < T["tr2"] + TR: return slide(form_em(t, T), ARTE0, (t - T["tr2"]) / TR)
    if t < T["tr3"]: return arte_em(t, T)
    if t < T["tr3"] + TR: return slide(arte_em(t, T), PRONTO, (t - T["tr3"]) / TR)
    if t < T["tr4"]: return PRONTO
    if t < T["tr4"] + TR: return slide(PRONTO, CARTOES, (t - T["tr4"]) / TR)
    return CARTOES

def toques(T):
    return [(T["tap_add"],    215, 668),            # "Adicionar cartão"
            (T["tap_num"],    DX + 100, 495),       # campo NÚMERO
            (T["tap_check"],  DX + 44, 756),        # "Esse é meu cartão principal"
            (T["tap_cont1"],  DX + 207, 831),       # "Continuar" do formulário
            (T["tap_arte"],   315, 349),            # arte "Amizade"
            (T["tap_cont2"],  215, 831),            # "Continuar" da arte
            (T["tap_salvar"], 215, 831)]            # "Salvar"

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
    open(os.path.join(OUT, "cadastrar-cartao.vtt"), "w").write(vtt(fala))

    textos = [bloco_texto(i) for i in range(len(LINHAS))]
    mp4 = os.path.join(OUT, "cadastrar-cartao.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    lista = toques(T); n = int(total * FPS)
    poster_f = int((T["tr4"] - 0.4) * FPS)          # "Seu cartão está pronto"
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, T).copy()
        desenhar_toques(tela, t, lista)
        destaque_cartao(tela, t, T)
        quadro = FUNDO.copy()
        quadro.paste(tela, (PX + BEZEL, PY + BEZEL), mask_tela)
        i, a = texto_em(t, fala)
        if a < 1 and i > 0:
            prev = textos[i - 1].copy(); prev.putalpha(prev.getchannel("A").point(lambda v: int(v * (1 - a))))
            quadro.alpha_composite(prev)
        cur = textos[i] if a >= 1 else textos[i].copy()
        if a < 1: cur.putalpha(cur.getchannel("A").point(lambda v: int(v * a)))
        quadro.alpha_composite(cur)
        fo = ramp(t, total - 0.5, total)
        if fo > 0: quadro.alpha_composite(Image.new("RGBA", (W, H), (247, 243, 253, int(255 * fo))))
        rgb = quadro.convert("RGB")
        ff.stdin.write(rgb.tobytes())
        if f == poster_f: rgb.save(os.path.join(OUT, "cadastrar-cartao.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for k, v in sorted(T.items(), key=lambda kv: kv[1]): print(f"  {k}: {v:.2f}")

if __name__ == "__main__":
    main()
