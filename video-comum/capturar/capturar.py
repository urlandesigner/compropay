"""Guarda a tela atual do iPhone (pelo Espelhamento do iPhone) como imagem. Não monta vídeo.

    capturar.py <fluxo> <nome> ["o que é esta tela"]      uma tela, agora
    capturar.py <fluxo> --observar [--ate SEGUNDOS]        você navega; cada tela que fica parada é salva
    capturar.py --listar

Salva em capturas-iphone/<fluxo>/NN-<nome>.png: só a tela útil do aparelho, em 2x
(~748x1626), PNG sem perda, cantos arredondados transparentes. A janela inteira, sem
recorte, fica em capturas-iphone/<fluxo>/janela/. Cada captura entra na tabela
capturas-iphone/<fluxo>/indice.md, na ordem.

A pasta capturas-iphone/ não vai para o Git (.git/info/exclude): as telas do app real
trazem nome, saldo e final de cartão. O que vai para a Wiki é o vídeo, depois da revisão.

Quem abre o Espelhamento do iPhone, deixa o app na tela certa e navega é a pessoa.
Este programa só tira o retrato do que está na janela agora.
"""
import argparse, os, re, subprocess, sys, tempfile, time, unicodedata
from datetime import datetime
import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAIZ = os.environ.get("CAPTURAS_DIR") or os.path.join(REPO, "capturas-iphone")

JXA = r'''
ObjC.import("CoreGraphics"); ObjC.import("Foundation");
const l = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
const j = l.filter(w => w.kCGWindowLayer === 0 && /Espelhamento do iPhone|iPhone Mirroring/i.test(w.kCGWindowOwnerName || ""));
JSON.stringify(j.map(w => ({id: w.kCGWindowNumber, h: w.kCGWindowBounds.Height})));
'''

def janela_id():
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA], capture_output=True, text=True)
    import json
    try: achadas = json.loads(r.stdout.strip() or "[]")
    except ValueError: achadas = []
    if not achadas:
        sys.exit("Não achei a janela do Espelhamento do iPhone. Abra o app e deixe a janela visível.")
    return max(achadas, key=lambda w: w["h"])["id"]            # a maior: a janela do aparelho

def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if not t: sys.exit("Nome inválido: use letras e números.")
    return t

def pausada(im):
    """True quando a janela mostra o próprio espelhamento, não o app: pausado, bloqueado, conectando.

    Essas telas são escuras (cinza liso, ou um degradê azul-marinho) e quase não têm branco: só
    um texto fino. O app é claro. Quando um aviso abre, o fundo do app escurece, mas o aviso é uma
    caixa branca grande, então: muito escuro E quase nada branco = é o espelhamento.
    Quem filma uma tela escura de verdade (câmera do QR code) usa --forcar.
    """
    a = np.array(im.convert("RGB")).astype(int); miolo = a[a.shape[0] // 8: -a.shape[0] // 8]
    escuro = float((miolo.max(axis=2) < 110).mean()); branco = float((miolo.min(axis=2) > 215).mean())
    return escuro > 0.60 and branco < 0.04

def tela_util(im):
    """Recorta ao contorno do aparelho. A margem da janela é transparente, então o alfa dá a caixa exata."""
    ys, xs = np.where(np.array(im)[..., 3] == 255)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

def listar():
    if not os.path.isdir(RAIZ): print("Nenhuma captura ainda."); return
    for f in sorted(os.listdir(RAIZ)):
        d = os.path.join(RAIZ, f)
        if os.path.isdir(d):
            n = len([x for x in os.listdir(d) if re.match(r"\d\d-.*\.png$", x)])
            print(f"{f}: {n} tela(s)")

def capturar_janela(wid):
    with tempfile.TemporaryDirectory() as tmp:
        bruto = os.path.join(tmp, "janela.png")
        r = subprocess.run(["screencapture", "-l", str(wid), "-o", "-x", bruto], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(bruto):
            sys.exit(f"screencapture falhou: {r.stderr.strip() or r.returncode}. Confira a permissão de Gravação de Tela.")
        janela = Image.open(bruto).convert("RGBA"); janela.load()
    return janela, tela_util(janela)

def salvar(fluxo, nome, janela, tela, nota):
    """Grava a captura com o próximo número do fluxo e acrescenta a linha no índice. Devolve o caminho."""
    pasta = os.path.join(RAIZ, fluxo); os.makedirs(os.path.join(pasta, "janela"), exist_ok=True)
    n = 1 + max([int(m.group(1)) for f in os.listdir(pasta) if (m := re.match(r"(\d\d)-.*\.png$", f))] or [0])
    arq = f"{n:02}-{nome}.png"
    tela.save(os.path.join(pasta, arq)); janela.save(os.path.join(pasta, "janela", arq))
    idx = os.path.join(pasta, "indice.md")
    if not os.path.exists(idx):
        open(idx, "w", encoding="utf-8").write(
            f"# Fluxo: {fluxo}\n\nTelas do app no iPhone, pelo Espelhamento do iPhone. PNG em 2x, só a tela do "
            f"aparelho, cantos transparentes. A janela inteira, sem recorte, fica em `janela/`.\n\n"
            f"| # | Arquivo | O que é | Tamanho | Capturada em |\n|---|---|---|---|---|\n")
    with open(idx, "a", encoding="utf-8") as f:
        f.write(f"| {n:02} | `{arq}` | {nota or '—'} | {tela.width}x{tela.height} | {datetime.now():%d/%m/%Y %H:%M} |\n")
    return os.path.join(pasta, arq)

def avisar_git(caminho):
    dentro = os.path.abspath(caminho).startswith(REPO + os.sep)
    if dentro and subprocess.run(["git", "-C", REPO, "check-ignore", "-q", caminho], stderr=subprocess.DEVNULL).returncode != 0:
        print("ATENÇÃO: capturas-iphone/ não está fora do Git. Rode: echo 'capturas-iphone/' >> .git/info/exclude")

def curto(tela):
    return np.array(tela.convert("RGB").resize((90, 195), Image.BILINEAR)).astype(int)

def diferenca(a, b):
    return float(np.abs(a - b).mean() / 255)

def observar(fluxo, ate, forcar):
    """Salva cada tela nova do app, depois que ela para de mexer.

    Uma tela conta como nova quando fica parada ~1 s e difere da última salva. O cursor piscando,
    o relógio e a animação de transição não contam: só o que muda de verdade.
    Para: Ctrl-C, o prazo (--ate) ou o arquivo capturas-iphone/<fluxo>/.parar
    """
    PARADA, NOVA, ESTAVEL, ESPERA, INTERVALO = 0.004, 0.010, 1.0, 0.45, 0.4
    wid = janela_id(); pasta = os.path.join(RAIZ, fluxo); os.makedirs(pasta, exist_ok=True)
    parar = os.path.join(pasta, ".parar")
    if os.path.exists(parar): os.remove(parar)
    ultimo = candidato = desde = None; salvas = 0; avisou_pausa = False; t0 = time.time()
    print(f"Observando o fluxo '{fluxo}'. Navegue no app; cada tela parada é salva. "
          f"Para parar: crie {os.path.relpath(parar, REPO) if parar.startswith(REPO) else parar} ou Ctrl-C.", flush=True)
    try:
        while time.time() - t0 < ate and not os.path.exists(parar):
            janela, tela = capturar_janela(wid)
            if pausada(tela) and not forcar:
                if not avisou_pausa: print("A janela não mostra o app (pausada, bloqueada ou conectando): clique em Retomar ou use o Touch ID.", flush=True); avisou_pausa = True
                time.sleep(ESPERA); continue
            avisou_pausa = False
            c = curto(tela)
            if candidato is None or diferenca(c, candidato) > PARADA: candidato, desde = c, time.time()
            elif time.time() - desde >= ESTAVEL and (ultimo is None or diferenca(candidato, ultimo) > NOVA):
                caminho = salvar(fluxo, "tela", janela, tela, "captura automática")
                ultimo = candidato; salvas += 1
                print(f"[{int(time.time() - t0):4}s] {os.path.basename(caminho)}", flush=True)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        pass
    print(f"Fim da observação: {salvas} tela(s) em {os.path.relpath(pasta, REPO) if pasta.startswith(REPO) else pasta}", flush=True)
    avisar_git(pasta)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fluxo", nargs="?"); ap.add_argument("nome", nargs="?"); ap.add_argument("nota", nargs="?", default="")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--observar", action="store_true", help="salva sozinho cada tela que ficar parada")
    ap.add_argument("--ate", type=int, default=900, help="segundos máximos da observação (padrão 900)")
    ap.add_argument("--forcar", action="store_true", help="salva mesmo que a tela pareça a de espelhamento pausado")
    a = ap.parse_args()
    if a.listar: return listar()
    if not a.fluxo: ap.error("informe o fluxo")
    fluxo = slug(a.fluxo)
    if a.observar: return observar(fluxo, a.ate, a.forcar)
    if not a.nome: ap.error("informe o nome da tela (ou use --observar)")

    janela, tela = capturar_janela(janela_id())
    if pausada(tela) and not a.forcar:
        sys.exit("A janela mostra o próprio espelhamento (pausado, bloqueado ou conectando), não o app. "
                 "Clique em Retomar, ou use o Touch ID se pedir, e tente de novo.")
    caminho = salvar(fluxo, slug(a.nome), janela, tela, a.nota)
    dentro = os.path.abspath(caminho).startswith(REPO + os.sep)
    print(f"{os.path.relpath(caminho, REPO) if dentro else caminho}  ({tela.width}x{tela.height})")
    avisar_git(os.path.dirname(caminho))

if __name__ == "__main__":
    main()
