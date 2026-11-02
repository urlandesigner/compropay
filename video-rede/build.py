"""Monta o vídeo "Como consultar a rede credenciada ComproPay e Comprocard?".

A tela inicial rola até Serviços, toca em Rede e abre a lista de
estabelecimentos. Na lista ninguém toca em nada: o holofote (o resto escurece)
mostra a busca e o primeiro estabelecimento.

Entrada: fig/home.png (430x1255) e fig/rede.png (414x896), do Figma.
Saída: out/rede-credenciada.mp4 (1920x1080, texto na lateral) + .vtt + .jpg
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
SW, SH = 430, 896                      # tela do app; a lista do Figma tem 896 de altura
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
FONT = os.path.join(COMUM, "fonts", "Inter-%s.otf")
def font(w, s): return ImageFont.truetype(FONT % w, s)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ---------------------------------------------------------------- roteiro
LINHAS = [
    "Na tela inicial, role até Serviços.",
    "Toque em Rede.",
    "Aparece a lista dos estabelecimentos credenciados.",
    "No topo, busque por nome, cidade ou bairro.",
    "Em cada um, você pode ligar ou ver no mapa onde fica.",
    "Pronto! É só escolher o estabelecimento.",
]
ROTULO = "Consultar a rede credenciada"
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
HOME = Image.open(os.path.join(FIG, "home.png")).convert("RGBA")
ALTA = HOME.size[1]                    # 1255
TOPO = 62                              # barra de status, não rola
TAB = 120                              # faixa do menu inferior, não rola
VISTA = SH - TOPO - TAB                # 714: altura da parte que rola
FIM_CONTEUDO = 1152                    # fim dos serviços (1128) mais a folga de baixo
ROLAGEM_MAX = FIM_CONTEUDO - TOPO - VISTA
ROLAGEM = 370                          # onde a tela para: Serviços inteiro à vista
assert ROLAGEM <= ROLAGEM_MAX, f"rolagem passa do fim do conteúdo ({ROLAGEM_MAX})"

BARRA = HOME.crop((0, 0, SW, TOPO))
MENU = HOME.crop((0, ALTA - TAB, SW, ALTA))

def home_em(s):
    """A tela inicial rolada s pixels, com status e menu fixos."""
    im = Image.new("RGBA", (SW, SH), "white")
    im.paste(BARRA, (0, 0))
    topo = int(round(TOPO + s))
    im.paste(HOME.crop((0, topo, SW, topo + VISTA)), (0, TOPO))
    im.paste(MENU, (0, SH - TAB))
    return im

def padronizar(im):
    """A lista sai do Figma com 414 de largura, não 430.

    Completa a diferença repetindo a coluna de cada borda — que é do mesmo
    cinza de fundo (ou do branco do cabeçalho) em cada linha, então a emenda
    não aparece. Esticar a tela deformaria o texto.
    """
    if im.width == SW: return im, 0
    falta = SW - im.width; esq = falta // 2; dire = falta - esq
    novo = Image.new("RGBA", (SW, SH))
    novo.paste(im, (esq, 0))
    novo.paste(im.crop((0, 0, 1, SH)).resize((esq, SH)), (0, 0))
    novo.paste(im.crop((im.width - 1, 0, im.width, SH)).resize((dire, SH)), (esq + im.width, 0))
    return novo, esq

LISTA, DX = padronizar(Image.open(os.path.join(FIG, "rede.png")).convert("RGBA"))

# Medidas na lista do Figma (414 de largura), deslocadas pelo preenchimento.
BUSCA   = (20 + DX - 4, 95 - 4, 393 + DX + 4, 139 + 4)       # campo "Buscar nome, cidade, bairro"
CARTAO1 = (15 + DX - 2, 191 - 2, 399 + DX + 2, 325 + 2)      # primeiro estabelecimento

def retangulo_servicos(s):
    """Onde o holofote fica nos Serviços, para uma dada rolagem (frame 848–1136)."""
    y0 = 848 - s; y1 = 1136 - s
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

# ---------------------------------------------------------------- animação
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

def montar_timeline(dur):
    """Tempos de fala e eventos, a partir da duração de cada frase."""
    T = {}; fala = []; t = 0.5
    def falar(i):
        nonlocal t
        s, e = t, t + dur[i]; fala.append((s, e)); return s, e

    s, e = falar(0); T["rola_ini"] = s + 0.15; T["rola_fim"] = s + 1.35; T["foco_serv"] = s + 1.0
    t = max(e, T["rola_fim"]) + 0.4

    s, e = falar(1); T["tap_rede"] = e + 0.15; T["tr1"] = T["tap_rede"] + 0.25
    t = T["tr1"] + 0.42 + 0.45

    s, e = falar(2)
    t = e + 0.4

    s, e = falar(3); T["foco_busca"] = s - 0.05
    t = e + 0.45

    s, e = falar(4); T["foco_cartao"] = s - 0.05
    t = e + 0.45

    s, e = falar(5); T["foco_fim"] = s - 0.05; T["fim"] = e + 1.6
    return fala, T

TR = 0.42   # duração da transição de tela
def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", (SW, SH), "black")
    im.alpha_composite(a, (int(-SW * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", (SW, SH), (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(SW * (1 - p)), 0))
    return im

def rolagem_em(t, T):
    return ROLAGEM * ease(ramp(t, T["rola_ini"], T["rola_fim"]))

def focos_em(t, T):
    """Lista de (retângulo, força) do holofote neste instante."""
    def forca(ini, fim):
        return ease(ramp(t, ini, ini + 0.3)) * (1 - ease(ramp(t, fim, fim + 0.25)))
    s = rolagem_em(t, T)
    return [
        (retangulo_servicos(s), forca(T["foco_serv"], T["tap_rede"] + 0.1), "home"),
        (BUSCA, forca(T["foco_busca"], T["foco_cartao"]), "lista"),
        (CARTAO1, forca(T["foco_cartao"], T["foco_fim"]), "lista"),
    ]

def tela_em(t, T):
    home = home_em(rolagem_em(t, T))
    for rect, f, onde in focos_em(t, T):
        if onde == "home": home = aplicar_foco(home, rect, f)
    lista = LISTA.copy()
    for rect, f, onde in focos_em(t, T):
        if onde == "lista": lista = aplicar_foco(lista, rect, f)
    if t < T["tr1"]: return home
    if t < T["tr1"] + TR: return slide(home, lista, (t - T["tr1"]) / TR)
    return lista

def toques(T):
    return [(T["tap_rede"], 60, 933 - ROLAGEM)]       # atalho "Rede", no centro do quadradinho

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
    open(os.path.join(OUT, "rede-credenciada.vtt"), "w").write(vtt(fala))

    textos = [bloco_texto(i) for i in range(len(LINHAS))]
    mp4 = os.path.join(OUT, "rede-credenciada.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    lista = toques(T); n = int(total * FPS)
    poster_f = int((T["foco_cartao"] + 1.0) * FPS)      # lista com o holofote no 1º estabelecimento
    for f in range(n):
        t = f / FPS
        tela = tela_em(t, T).copy()
        desenhar_toques(tela, t, lista)
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
        if f == poster_f: rgb.save(os.path.join(OUT, "rede-credenciada.jpg"), quality=88)
        if "--prever" in sys.argv and f % 15 == 0:
            rgb.save(os.path.join(OUT, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)
    for k, v in sorted(T.items(), key=lambda kv: kv[1]): print(f"  {k}: {v:.2f}")

if __name__ == "__main__":
    main()
