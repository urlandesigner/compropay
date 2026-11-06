#!/usr/bin/env python3
"""Gera as páginas das perguntas (perguntas/<id>.html) e a lista do index.html.

A fonte das respostas é conteudo/perguntas.html: edite lá e rode de novo.
    python3 tools/gerar-perguntas.py

Cada <details> da fonte vira uma página com migalhas, passo a passo numerado, vídeo,
"Isso ajudou?", perguntas relacionadas e o bloco de atendimento, e uma linha na lista do index.html.
Data opcional: data-atualizado="2026-10-28" no <details> mostra "Atualizado em 28/10/2026" na página
e põe a pergunta em "Atualizadas recentemente" no index.html (as 5 mais recentes).
Mais buscados: data-mais-buscada="1" (ou 2, 3) no <details> põe a pergunta num dos 3 cards sob a busca do index.html.
"""
import html, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'perguntas'

INDEX = RAIZ / 'index.html'
src = INDEX.read_text(encoding='utf-8')
fonte = (RAIZ / 'conteudo' / 'perguntas.html').read_text(encoding='utf-8')

def bloco(inicio, fim):
    i = src.index(inicio)
    return src[i:src.index(fim, i) + len(fim)]

def caminhos(h):
    """Do index para uma página dentro de perguntas/."""
    h = re.sub(r'(src|srcset|href)="(assets/|DS%20wiki/)', r'\1="../\2', h)
    return h.replace('href="./"', 'href="../"')

header = caminhos(bloco('<header class="site-header">', '</header>'))
footer = caminhos(bloco('<footer class="cp-footer">', '</footer>'))
suporte = bloco('<section class="cp-panel faq-suporte"', '</section>')
categorias = dict(re.findall(r'<button type="button" class="cp-chip" data-cat="([^"]+)"[^>]*>(.*?)</button>', src))

itens = []
for m in re.finditer(r'<details id="([^"]+)" data-categoria="([^"]*)"([^>]*)>\s*<summary>.*?<span class="faq-q__titulo">(.*?)</span>.*?</summary>\s*<div class="cp-accordion__body">\n(.*?)\n            </div>\s*</details>', fonte, re.S):
    i, cat, extra, titulo, corpo = m.groups()
    atual = re.search(r'data-atualizado="(\d{4})-(\d{2})-(\d{2})"', extra)
    mais = re.search(r'data-mais-buscada="(\d+)"', extra)
    itens.append(dict(id=i, cat=cat, titulo=titulo, corpo=corpo, mais=int(mais.group(1)) if mais else 0,
                      atualizado=f'{atual.group(3)}/{atual.group(2)}/{atual.group(1)}' if atual else '',
                      iso=f'{atual.group(1)}-{atual.group(2)}-{atual.group(3)}' if atual else ''))
if not itens:
    sys.exit('Nenhuma pergunta encontrada em conteudo/perguntas.html')

def passo_a_passo(corpo):
    """Parágrafos "1- texto" viram uma lista numerada; o resto fica como está."""
    linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
    saida, grupo, inicio = [], [], 1
    def fecha():
        nonlocal grupo
        if grupo:
            saida.append(f'<ol class="pergunta__passos"' + (f' start="{inicio}"' if inicio != 1 else '') + '>\n' + '\n'.join(grupo) + '\n</ol>')
            grupo = []
    for l in linhas:
        n = re.match(r'<p>(\d+)\s?-\s*(.*)</p>$', l)
        if n:
            if not grupo: inicio = int(n.group(1))
            grupo.append(f'<li>{n.group(2)}</li>')
        else:
            fecha(); saida.append(l)
    fecha()
    return '\n'.join(saida)

def video_antes_da_lista(corpo):
    """O vídeo é o formato principal da resposta: sobe para logo antes da lista de passos que ele ilustra.

    Na fonte (conteudo/perguntas.html) o vídeo fica no fim de cada seção, depois dos passos; aqui ele
    vai para antes da lista, e o fechamento ("Pronto!") continua depois dela. Uma resposta com duas
    listas e dois vídeos (bloquear e desbloquear) leva cada vídeo para antes da sua lista.
    """
    padrao = re.compile(r'<div class="faq-video">.*?</div>', re.S)
    pos = 0
    while True:
        v = padrao.search(corpo, pos)
        if not v:
            return corpo
        lista = corpo.rfind('<ol ', pos, v.start())
        if lista == -1:                       # vídeo sem lista antes dele: fica onde está
            pos = v.end()
            continue
        bloco = v.group(0)
        corpo = corpo[:lista] + bloco + '\n' + corpo[lista:v.start()].rstrip('\n') + corpo[v.end():]
        pos = lista + len(bloco)

def resumo(corpo):
    p = re.search(r'<p>(.*?)</p>', corpo, re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '', p.group(1))) if p else ''
    t = re.sub(r'\s+', ' ', t).strip()
    return html.escape(t if len(t) <= 155 else t[:155].rsplit(' ', 1)[0] + '…', quote=True)

PAGINA = '''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titulo_txt} — Ajuda ComproPay</title>
  <meta name="description" content="{resumo}">
  <!-- Gerado por tools/gerar-perguntas.py a partir do index.html. Não edite aqui. -->
  <link rel="stylesheet" href="../DS%20wiki/tokens/fonts.css">
  <link rel="stylesheet" href="../DS%20wiki/dist/cp-tokens.css">
  <link rel="stylesheet" href="../DS%20wiki/dist/cp-components.css">
  <link rel="stylesheet" href="../DS%20wiki/icons/cp-icons.css">
  <link rel="stylesheet" href="../assets/site.css">
</head>
<body>
  <a class="cp-skip-link" href="#conteudo">Pular para o conteúdo</a>
  {header}

  <main id="conteudo" tabindex="-1">
    <div class="cp-page pergunta">
      <div class="pergunta__topo">
        <a class="cp-btn cp-btn--secondary cp-btn--sm cp-btn--voltar" href="../" data-voltar aria-label="Voltar"><svg class="cp-icon cp-icon--sm" aria-hidden="true"><use href="../DS%20wiki/icons/cp-icons.svg#cp-chevron-left"/></svg></a>
        <nav class="cp-crumb" aria-label="Breadcrumb">
          <ol>
            <li><a href="../">Ajuda</a></li>
            <li><a href="../?categoria={cat}">{cat_nome}</a></li>
            <li><span aria-current="page">{titulo}</span></li>
          </ol>
        </nav>
      </div>

      <article class="pergunta__artigo" id="{id}" data-faq-item>
        <p class="pergunta__selos"><a class="cp-badge cp-badge--soft" href="../?categoria={cat}">{cat_nome}</a></p>
        <h1 class="pergunta__titulo">{titulo}</h1>{atualizado}
        <div class="pergunta__corpo">
{corpo}
        </div>
      </article>
{relacionadas}
      {suporte}

      <p class="pergunta__voltar"><a class="cp-link" href="../">← Ver todas as dúvidas</a></p>
    </div>
  </main>

  {footer}
  <script src="../assets/config.js"></script>
  <script src="../assets/ajuda.js" defer></script>
</body>
</html>
'''

SAIDA.mkdir(exist_ok=True)
for antigo in SAIDA.glob('*.html'):
    antigo.unlink()

for k, it in enumerate(itens):
    # relacionadas: até 3 da mesma categoria, na ordem do index a partir desta
    mesma = [o for o in itens[k + 1:] + itens[:k] if o['cat'] == it['cat']][:3]
    rel = ''
    if mesma:
        li = '\n'.join(
            f'          <li><a class="cp-panel cartao-relacionada" href="{o["id"]}.html">'
            f'<span class="cartao-relacionada__titulo">{o["titulo"]}</span>'
            f'<span class="cartao-relacionada__acao">Ver resposta <svg class="cp-icon cp-icon--sm" aria-hidden="true"><use href="../DS%20wiki/icons/cp-icons.svg#cp-arrow-right"/></svg></span></a></li>'
            for o in mesma)
        rel = f'''
      <section class="pergunta__relacionadas" aria-labelledby="rel-titulo">
        <h2 id="rel-titulo" class="bloco-titulo">Perguntas relacionadas</h2>
        <ul class="relacionadas">
{li}
        </ul>
      </section>
'''
    atual = f'\n        <p class="pergunta__meta">Atualizado em {it["atualizado"]}</p>' if it['atualizado'] else ''
    corpo = video_antes_da_lista(passo_a_passo(it['corpo']))
    corpo = '\n'.join('          ' + l for l in corpo.split('\n'))
    texto = html.unescape(re.sub(r'<[^>]+>', '', it['titulo']))
    (SAIDA / f'{it["id"]}.html').write_text(PAGINA.format(
        titulo_txt=html.escape(texto), titulo=it['titulo'], resumo=resumo(it['corpo']), id=it['id'],
        cat=it['cat'], cat_nome=categorias[it['cat']],
        atualizado=atual, corpo=corpo, relacionadas=rel,
        header=header, footer=footer, suporte=suporte), encoding='utf-8')

print(f'{len(itens)} páginas em {SAIDA.relative_to(RAIZ)}/')

# Lista do index.html: um link por pergunta. data-busca leva o texto da resposta para a busca da página.
def texto(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()

linhas = []
for it in itens:
    busca = html.escape(texto(it['titulo'] + ' ' + it['corpo']), quote=True)
    linhas.append(f'''          <li id="{it['id']}" data-categoria="{it['cat']}" data-busca="{busca}">
            <a class="faq-item" href="perguntas/{it['id']}.html"><span class="faq-q"><span class="faq-q__titulo">{it['titulo']}</span><span class="cp-badge cp-badge--soft">{categorias[it['cat']]}</span></span><svg class="cp-icon cp-icon--md faq-item__seta" aria-hidden="true"><use href="DS%20wiki/icons/cp-icons.svg#cp-chevron-right"/></svg></a>
          </li>''')
def entre(texto_, ini, fim, conteudo):
    a, b = texto_.index(ini) + len(ini), texto_.index(fim)
    return texto_[:a] + '\n' + conteudo + '\n          ' + texto_[b:]

# Atualizadas recentemente: as 5 perguntas com data mais nova.
recentes = sorted([it for it in itens if it['iso']], key=lambda it: it['iso'], reverse=True)[:5]
li_recentes = '\n'.join(
    f'          <li><a class="cp-link" href="perguntas/{it["id"]}.html">{it["titulo"]}</a>'
    f' <span class="cp-badge cp-badge--soft">{categorias[it["cat"]]}</span>'
    f' <time datetime="{it["iso"]}">{it["atualizado"]}</time></li>' for it in recentes)

# Mais buscados: os 3 cards sob a busca, na ordem de data-mais-buscada.
mais_buscados = sorted([it for it in itens if it['mais']], key=lambda it: it['mais'])
if len(mais_buscados) > 3:
    print(f'Aviso: {len(mais_buscados)} perguntas com data-mais-buscada; só as 3 primeiras entram.', file=sys.stderr)
    mais_buscados = mais_buscados[:3]
li_mais = '\n'.join(
    f'            <li><a class="cp-panel faq-popular" href="perguntas/{it["id"]}.html"><span class="faq-popular__titulo">{it["titulo"]}</span>'
    f'<svg class="cp-icon cp-icon--md faq-popular__seta" aria-hidden="true"><use href="DS%20wiki/icons/cp-icons.svg#cp-chevron-right"/></svg></a></li>'
    for it in mais_buscados)

saida = entre(src, '<!-- LISTA:INICIO (gerada por tools/gerar-perguntas.py, não edite) -->', '<!-- LISTA:FIM -->', '\n'.join(linhas))
saida = entre(saida, '<!-- MAIS-BUSCADOS:INICIO -->', '<!-- MAIS-BUSCADOS:FIM -->', li_mais)
saida = entre(saida, '<!-- RECENTES:INICIO -->', '<!-- RECENTES:FIM -->', li_recentes) if li_recentes else entre(saida, '<!-- RECENTES:INICIO -->', '<!-- RECENTES:FIM -->', '')
INDEX.write_text(saida, encoding='utf-8')
print(f'{len(itens)} itens na lista, {len(recentes)} em "Atualizadas recentemente", {len(mais_buscados)} em "Mais buscados"')
