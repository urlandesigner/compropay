"""Monta um vídeo da Wiki a partir de um roteiro .yaml.

Em vez de um build.py por vídeo, cada vídeo traz só o roteiro: as telas, as
frases da narração e o que acontece em cada uma (rolar, tocar, destacar).
O resto é igual em todos: narração (Kokoro, pt-BR), legenda .vtt, aparelho,
transição, círculo de toque, holofote, pôster e uma folha de revisão.

    python montar.py ../../video-rede/roteiro.yaml
    python montar.py roteiro.yaml --so-revisao     # só a folha, sem voz nem vídeo

O formato do roteiro está em README.md, ao lado deste arquivo.
"""
import argparse, os, subprocess, sys
import numpy as np
import soundfile as sf
import imageio_ffmpeg
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageFilter

COMUM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # video-comum/
FPS, W, H = 30, 1920, 1080
ROXO = (113, 32, 209); TINTA = (33, 20, 56)
TR = 0.42                                    # duração da transição de tela
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def font(w, s): return ImageFont.truetype(os.path.join(COMUM, "fonts", f"Inter-{w}.otf"), s)
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

# ---------------------------------------------------------------- telas
def padronizar(im, largura):
    """Leva a tela à largura do aparelho sem esticar.

    O Figma e o iPhone nem sempre entregam 430 de largura (várias telas do app
    saem com 414). Completa a diferença repetindo a coluna de cada borda, que
    em cada linha é do mesmo fundo, então a emenda não aparece. Esticar
    deformaria o texto.
    """
    if im.width == largura: return im
    falta = largura - im.width
    if falta < 0: raise SystemExit(f"tela com {im.width}px de largura, maior que o aparelho ({largura}px)")
    esq = falta // 2; dire = falta - esq; h = im.height
    novo = Image.new("RGBA", (largura, h))
    novo.paste(im, (esq, 0))
    if esq: novo.paste(im.crop((0, 0, 1, h)).resize((esq, h)), (0, 0))
    if dire: novo.paste(im.crop((im.width - 1, 0, im.width, h)).resize((dire, h)), (esq + im.width, 0))
    return novo

def abrir(caminho, largura):
    return padronizar(Image.open(caminho).convert("RGBA"), largura)

# ---- telas capturadas do iPhone (Espelhamento do iPhone) --------------------------------------
# A janela espelhada traz uma margem branca em volta do aparelho. Nas medidas de 03/11/2026
# (janela no tamanho máximo, 391x860), a tela útil é 376x814, com cantos de raio ~50. Se o
# tamanho da janela mudar, passe `captura: { recorte: [x0, y0, x1, y1] }` na tela.
RECORTE_IPHONE = (10, 40, 382, 850)    # 2 px por dentro: o fio cinza da borda da janela não entra
RAIO_IPHONE = 44

def preencher_cantos(im, r):
    """Troca o que sobra fora do canto arredondado pela cor logo dentro dele, na mesma direção.

    O aparelho do vídeo tem o próprio canto; sem isso, a margem branca da captura
    apareceria como uma fatia clara em cada canto.
    """
    a = np.array(im.convert("RGB")); h, w = a.shape[:2]; out = a.copy()
    for cx, cy, sx, sy in [(r, r, -1, -1), (w - 1 - r, r, 1, -1), (r, h - 1 - r, -1, 1), (w - 1 - r, h - 1 - r, 1, 1)]:
        for y in range(cy - r, cy + 1) if sy < 0 else range(cy, cy + r + 1):
            for x in range(cx - r, cx + 1) if sx < 0 else range(cx, cx + r + 1):
                dx, dy = x - cx, y - cy; d = (dx * dx + dy * dy) ** 0.5
                if d > r - 1:
                    k = (r - 2.5) / d
                    out[y, x] = a[int(round(cy + dy * k)), int(round(cx + dx * k))]
    return Image.fromarray(out).convert("RGBA")

def abrir_captura(caminho, largura, altura, spec):
    """Captura do iPhone -> tela do aparelho.

    Formato do capturar.py (PNG 2x, já recortado ao aparelho, cantos transparentes): só preenche os
    cantos e ajusta à escala do vídeo. Formato antigo (janela inteira em 1x, 391x860): recorta antes.
    """
    c = spec if isinstance(spec, dict) else {}
    im = Image.open(caminho).convert("RGBA")
    if "recorte" not in c and im.getpixel((0, 0))[3] == 0:
        im = preencher_cantos(im, c.get("raio", int(im.width * 0.1444)))      # raio medido: ~108 px em 748
    else:
        im = preencher_cantos(im.crop(tuple(c.get("recorte", RECORTE_IPHONE))), c.get("raio", RAIO_IPHONE))
    return im.resize((largura, altura), Image.LANCZOS)

def trocar_barra(im, caminho_barra, altura, largura):
    """Põe uma barra de status limpa (9:41) no lugar da real (hora, bateria, ilha dinâmica).

    Pega só o que é desenho na barra de origem (hora, sinal, bateria) e coloca sobre a cor de
    fundo da própria tela, lida logo abaixo da barra. Em cabeçalho escuro (o roxo do app) os
    ícones saem claros, como no iPhone.
    """
    a = np.array(im.convert("RGB")).astype(int)
    src = np.array(abrir(caminho_barra, largura).convert("RGB")).astype(int)[:altura]
    cores, n = np.unique(src.reshape(-1, 3), axis=0, return_counts=True)
    fundo_src = cores[n.argmax()]                           # a cor que mais aparece = o fundo da barra
    fundo_tela = a[altura + 3, 6]                           # o cabeçalho, logo abaixo da barra
    lum = 0.299 * fundo_tela[0] + 0.587 * fundo_tela[1] + 0.114 * fundo_tela[2]
    dif = (src - fundo_src) if lum >= 90 else (fundo_src - src)             # fundo escuro: ícones claros
    a[:altura] = np.clip(fundo_tela + dif, 0, 255)
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")

def aplicar_mascaras(im, mascaras, base, largura):
    """Esconde dado pessoal. Coordenadas na tela já com a largura do aparelho.

    borrar (padrão): borra o retângulo. cobrir: tampa com uma cor lisa. trocar: apaga o texto e escreve
    outro, fictício (`texto`, `tam`, `peso`, `cor`, `alinhar`); o fundo é a cor em volta do retângulo.
    colar: cola o mesmo retângulo de outra imagem (ex.: a tela do Figma, que
    tem dados fictícios), quando o layout das duas bate.
    """
    im = im.copy()
    for m in mascaras or []:
        x0, y0, x1, y1 = m["rect"]; modo = m.get("modo", "borrar")
        if modo == "borrar":
            im.paste(im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(m.get("raio", 10))), (x0, y0))
        elif modo == "cobrir":
            ImageDraw.Draw(im).rounded_rectangle((x0, y0, x1, y1), 6, fill=tuple(m.get("cor", [236, 236, 240])))
        elif modo == "trocar":
            arr = np.array(im.crop((x0, y0, x1, y1)).convert("RGB")).astype(int)
            borda = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
            fundo_ret = tuple(int(v) for v in np.median(borda, axis=0))               # a cor em volta do texto
            d = ImageDraw.Draw(im); d.rectangle((x0, y0, x1, y1), fill=fundo_ret)
            f = font(m.get("peso", "Regular"), m.get("tam", 14)); alinhar = m.get("alinhar", "esq")
            xx, anc = {"esq": (x0 + 2, "lm"), "dir": (x1 - 2, "rm"), "centro": ((x0 + x1) / 2, "mm")}[alinhar]
            d.text((xx, (y0 + y1) / 2), m["texto"], font=f, fill=tuple(m.get("cor", [33, 20, 56])), anchor=anc)
        elif modo == "colar":
            outra = abrir(os.path.join(base, m["de"]), largura)
            im.paste(outra.crop((x0, y0, x1, y1)), (x0, y0))
        else:
            raise SystemExit(f"máscara com modo desconhecido: {modo}")
    return im

class Tela:
    def __init__(self, nome, spec, base, SW, SH):
        self.nome, self.SW, self.SH = nome, SW, SH
        caminho = os.path.join(base, spec["fonte"])
        if spec.get("captura"):
            self.bruta = abrir_captura(caminho, SW, SH, spec["captura"])
        else:
            self.bruta = abrir(caminho, SW)
        if spec.get("barra_status"):
            b = spec["barra_status"]
            self.bruta = trocar_barra(self.bruta, os.path.join(base, b["de"]), b.get("altura", 50), SW)
        self.mascaras = spec.get("mascara") or []
        self.img = aplicar_mascaras(self.bruta, self.mascaras, base, SW)
        self.focos = spec.get("focos", {})
        self.topo = spec.get("fixo_topo", 0); self.base = spec.get("fixo_base", 0)
        self.rolavel = bool(self.topo or self.base)
        if self.rolavel:
            self.alta = self.img.height
            self.vista = SH - self.topo - self.base
            self.fim_conteudo = spec.get("fim_conteudo", self.alta - self.base)
            self.rolagem_max = self.fim_conteudo - self.topo - self.vista
            self.barra = self.img.crop((0, 0, SW, self.topo))
            self.menu = self.img.crop((0, self.alta - self.base, SW, self.alta))
        elif self.img.height != SH:
            raise SystemExit(f"tela '{nome}' tem {self.img.height}px de altura e o aparelho {SH}px. "
                             f"Ajuste 'aparelho.altura' ou marque a tela como rolável (fixo_topo/fixo_base).")

    def render(self, s=0.0):
        """A tela, rolada s pixels se for rolável. Sempre devolve uma cópia."""
        if not self.rolavel: return self.img.copy()
        im = Image.new("RGBA", (self.SW, self.SH), "white")
        im.paste(self.barra, (0, 0))
        topo = int(round(self.topo + s))
        im.paste(self.img.crop((0, topo, self.SW, topo + self.vista)), (0, self.topo))
        im.paste(self.menu, (0, self.SH - self.base))
        return im

def resolver_foco(spec, tela, s):
    """Retângulo do holofote, na tela do aparelho. Aceita nome, [x0,y0,x1,y1] ou {rola: [y0,y1]}."""
    if isinstance(spec, str): spec = tela.focos[spec]
    if isinstance(spec, dict) and "rola" in spec:       # faixa do conteúdo rolável, em coordenadas da imagem
        y0, y1 = spec["rola"]; x0, x1 = spec.get("x", [14, 416])
        return (float(x0), max(y0 - s, tela.topo - 6), float(x1), min(y1 - s, tela.SH - tela.base - 6))
    return tuple(float(v) for v in spec)

def aplicar_foco(im, rect, forca):
    if rect is None or forca <= 0.01: return im
    x0, y0, x1, y1 = rect
    if y1 - y0 < 8: return im
    sombra = Image.new("L", im.size, int(170 * forca))
    ImageDraw.Draw(sombra).rounded_rectangle((x0, y0, x1, y1), 18, fill=0)
    capa = Image.new("RGBA", im.size, (16, 5, 38, 255)); capa.putalpha(sombra)
    im.alpha_composite(capa)
    ImageDraw.Draw(im, "RGBA").rounded_rectangle((x0, y0, x1, y1), 18, outline=(178, 126, 248, int(215 * forca)), width=3)
    return im

# ---------------------------------------------------------------- linha do tempo
def montar_timeline(passos, dur, tela_inicial):
    """Tempos de cada evento, a partir da duração de cada frase.

    fala: onde cada frase cai. rolagens: por tela, (início, fim, alvo).
    focos: holofotes, com entrada e saída. toques: (t, x, y).
    trocas: (t, de, para), a tela desliza ao tocar em algo que tem 'vai_para'.
    """
    t = 0.5; fala, focos, toques, trocas, rolagens = [], [], [], [], {}
    atual = tela_inicial; foco_atual = None
    for i, p in enumerate(passos):
        s, e = t, t + dur[i]; fala.append((s, e)); fim_passo = e
        pausa = p.get("pausa", 0.45)

        if "rolar" in p:
            rolagens.setdefault(atual, []).append((s + 0.15, s + 1.35, float(p["rolar"])))
            fim_passo = max(fim_passo, s + 1.35)

        if "foco" in p:
            if foco_atual is not None: focos[foco_atual]["saida"] = s - 0.05       # um holofote cede ao próximo
            entrada = s + 1.0 if "rolar" in p else s - 0.05                        # com rolagem, só acende depois dela
            focos.append({"tela": atual, "spec": p["foco"], "entrada": entrada, "saida": None})
            foco_atual = len(focos) - 1
        elif "toque" not in p and foco_atual is not None:                          # passo sem holofote e sem toque o encerra
            focos[foco_atual]["saida"] = s - 0.05; foco_atual = None

        if "toque" in p:
            tq = p["toque"]; quando = None
            if isinstance(tq, dict): quando = tq.get("quando"); tq = tq["em"]
            t_tap = (e + 0.15) if quando is None else (s + quando)
            toques.append((t_tap, float(tq[0]), float(tq[1])))
            fim_passo = max(fim_passo, t_tap)
            if "vai_para" in p:
                tr = t_tap + 0.25; trocas.append((tr, atual, p["vai_para"]))
                if foco_atual is not None: focos[foco_atual]["saida"] = t_tap + 0.1; foco_atual = None
                atual = p["vai_para"]; t = tr + TR + pausa
                continue
        t = fim_passo + pausa

    total = fala[-1][1] + 1.6
    for f in focos:
        if f["saida"] is None: f["saida"] = total - 0.6
    return fala, focos, toques, trocas, rolagens, total

def rolagem_em(eventos, t):
    v0 = 0.0
    for ini, fim, alvo in eventos:
        if t >= fim: v0 = alvo; continue
        if t > ini: return v0 + (alvo - v0) * ease(ramp(t, ini, fim))
        return v0
    return v0

def slide(a, b, p):
    p = ease(p); im = Image.new("RGBA", a.size, "black"); w = a.width
    im.alpha_composite(a, (int(-w * 0.3 * p), 0))
    im.alpha_composite(Image.new("RGBA", a.size, (0, 0, 0, int(90 * p))))
    im.alpha_composite(b, (int(w * (1 - p)), 0))
    return im

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

# ---------------------------------------------------------------- aparelho e texto
BEZEL, R_TELA = 12, 50

def fundo(PX, PY, PW, PH):
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    c1, c2 = np.array([247, 243, 253]), np.array([234, 224, 250])
    t = np.clip(0.6 * x + 0.4 * y, 0, 1)[..., None]
    bg = Image.fromarray((c1 * (1 - t) + c2 * t).astype(np.uint8), "RGB").convert("RGBA")
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((PX + 10, PY + 30, PX + PW + 10, PY + PH + 30), R_TELA + BEZEL, fill=(60, 20, 110, 70))
    bg.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(28)))
    ImageDraw.Draw(bg).rounded_rectangle((PX, PY, PX + PW, PY + PH), R_TELA + BEZEL, fill=(22, 18, 30))
    return bg

TX, TW = 1000, 780
def bloco_texto(linha, rotulo):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font("SemiBold", 60); linhas, cur = [], ""
    for p in linha.split():
        tentativa = (cur + " " + p).strip()
        if d.textlength(tentativa, font=f) > TW and cur: linhas.append(cur); cur = p
        else: cur = tentativa
    linhas.append(cur)
    y0 = H // 2 - len(linhas) * 78 // 2 + 20
    d.text((TX, y0 - 70), rotulo.upper(), font=font("SemiBold", 22), fill=ROXO)
    for j, l in enumerate(linhas): d.text((TX, y0 + j * 78), l, font=f, fill=TINTA)
    return im

def texto_em(t, fala):
    """Índice da frase visível e opacidade (troca suave entre frases)."""
    i = 0
    for k, (s, e) in enumerate(fala):
        if t >= s - 0.25: i = k
    return i, ease(ramp(t, fala[i][0] - 0.25, fala[i][0] + 0.05))

def vtt(fala, linhas):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
    out = ["WEBVTT", ""]
    for i, (s, e) in enumerate(fala):
        fim = fala[i + 1][0] - 0.05 if i + 1 < len(fala) else e + 1.2
        out.append(f"{i+1}\n{ts(s)} --> {ts(fim)}\n{linhas[i]}\n")
    return "\n".join(out)

# ---------------------------------------------------------------- narração
def narrar(linhas, voz):
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(COMUM, "tts/kokoro-v1.0.onnx"), os.path.join(COMUM, "tts/voices-v1.0.bin"))
    clips = []
    for txt in linhas:
        s, sr = k.create(txt, voice=voz, speed=1.0, lang="pt-br")
        idx = np.where(np.abs(s) > 0.01)[0]                      # corta o silêncio das pontas
        clips.append(s[max(idx[0] - 600, 0): idx[-1] + 1200])
    return clips, sr

# ---------------------------------------------------------------- revisão
def folha_revisao(telas, saida):
    """Uma folha com cada tela como vai aparecer no vídeo, e as máscaras contornadas.

    É o que se confere antes de qualquer coisa ir para a Wiki: nome, saldo,
    final de cartão, notificação que passou na barra de cima.
    """
    alt = 640; itens = []
    for nome, tela in telas.items():
        im = tela.img.convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
        for m in tela.mascaras:
            d.rectangle(m["rect"], outline=(230, 30, 30, 255), width=3)
        esc = alt / im.height; itens.append((nome, im.resize((max(int(im.width * esc), 1), alt), Image.LANCZOS)))
    larg = sum(i.width for _, i in itens) + 24 * (len(itens) + 1)
    folha = Image.new("RGB", (larg, alt + 90), (247, 243, 253)); d = ImageDraw.Draw(folha); x = 24
    for nome, im in itens:
        folha.paste(im, (x, 60)); d.text((x, 20), nome, font=font("SemiBold", 22), fill=TINTA); x += im.width + 24
    folha.save(saida, quality=90)

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roteiro"); ap.add_argument("--saida")
    ap.add_argument("--so-revisao", action="store_true"); ap.add_argument("--prever", action="store_true")
    a = ap.parse_args()

    base = os.path.dirname(os.path.abspath(a.roteiro))
    r = yaml.safe_load(open(a.roteiro, encoding="utf-8"))
    out = a.saida or os.path.join(base, "out"); os.makedirs(out, exist_ok=True)
    nome = r["video"]; SW, SH = r.get("aparelho", {}).get("largura", 430), r.get("aparelho", {}).get("altura", 896)
    telas = {n: Tela(n, s, base, SW, SH) for n, s in r["telas"].items()}
    passos = r["passos"]; linhas = [p["fala"] for p in passos]
    tela_inicial = passos[0].get("tela") or next(iter(telas))

    folha_revisao(telas, os.path.join(out, "revisao.jpg"))
    print("folha de revisão ->", os.path.join(out, "revisao.jpg"))
    if a.so_revisao: return

    clips, sr = narrar(linhas, r.get("voz", "pf_dora"))
    dur = [len(c) / sr for c in clips]
    fala, focos, toques, trocas, rolagens, total = montar_timeline(passos, dur, tela_inicial)
    for n, evs in rolagens.items():
        mx = telas[n].rolagem_max
        if any(alvo > mx for _, _, alvo in evs): raise SystemExit(f"rolagem de '{n}' passa do fim do conteúdo ({mx})")

    audio = np.zeros(int((total + 0.5) * sr), dtype=np.float32)
    for (s, _), c in zip(fala, clips):
        i = int(s * sr); audio[i:i + len(c)] += c
    wav = os.path.join(out, "narracao.wav"); sf.write(wav, audio, sr)
    open(os.path.join(out, f"{nome}.vtt"), "w", encoding="utf-8").write(vtt(fala, linhas))

    PW, PH = SW + 2 * BEZEL, SH + 2 * BEZEL; PX, PY = 380, (H - PH) // 2
    mask_tela = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(mask_tela).rounded_rectangle((0, 0, SW - 1, SH - 1), R_TELA, fill=255)
    FUNDO = fundo(PX, PY, PW, PH)
    textos = [bloco_texto(l, r["rotulo"]) for l in linhas]

    def render(n, t):
        tela = telas[n]; s = rolagem_em(rolagens.get(n, []), t) if tela.rolavel else 0.0
        im = tela.render(s)
        for f in focos:
            if f["tela"] != n: continue
            forca = ease(ramp(t, f["entrada"], f["entrada"] + 0.3)) * (1 - ease(ramp(t, f["saida"], f["saida"] + 0.25)))
            if forca > 0.01: im = aplicar_foco(im, resolver_foco(f["spec"], tela, s), forca)
        return im

    def tela_em(t):
        atual = tela_inicial
        for tr, de, para in trocas:
            if t >= tr + TR: atual = para; continue
            if t >= tr: return slide(render(de, t), render(para, t), (t - tr) / TR)
            break
        return render(atual, t)

    pst = r.get("poster", {}); ip = pst.get("passo", max(len(passos) - 2, 0))
    poster_f = int((fala[ip][0] + pst.get("apos", 1.0)) * FPS)

    mp4 = os.path.join(out, f"{nome}.mp4")
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    for f in range(int(total * FPS)):
        t = f / FPS
        tela = tela_em(t); desenhar_toques(tela, t, toques)
        quadro = FUNDO.copy(); quadro.paste(tela, (PX + BEZEL, PY + BEZEL), mask_tela)
        i, al = texto_em(t, fala)
        if al < 1 and i > 0:
            prev = textos[i - 1].copy(); prev.putalpha(prev.getchannel("A").point(lambda v: int(v * (1 - al))))
            quadro.alpha_composite(prev)
        cur = textos[i] if al >= 1 else textos[i].copy()
        if al < 1: cur.putalpha(cur.getchannel("A").point(lambda v: int(v * al)))
        quadro.alpha_composite(cur)
        fo = ramp(t, total - 0.5, total)
        if fo > 0: quadro.alpha_composite(Image.new("RGBA", (W, H), (247, 243, 253, int(255 * fo))))
        rgb = quadro.convert("RGB"); ff.stdin.write(rgb.tobytes())
        if f == poster_f: rgb.save(os.path.join(out, f"{nome}.jpg"), quality=88)
        if a.prever and f % 15 == 0: rgb.save(os.path.join(out, f"q{f:04}.jpg"), quality=80)
    ff.stdin.close(); ff.wait()
    print("duração", round(total, 2), "s ->", mp4)

if __name__ == "__main__":
    main()
