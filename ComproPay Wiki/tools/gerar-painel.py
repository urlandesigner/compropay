#!/usr/bin/env python3
"""Gera a planilha que alimenta o painel de vídeos da Wiki.

    python3 tools/gerar-painel.py

Lê conteudo/perguntas.html, a mesma fonte do gerar-perguntas.py, e escreve
tools/perguntas-video.csv com uma linha por pergunta: número, título,
categoria, situação do vídeo e o arquivo, quando existe.

A situação sai da resposta de cada pergunta:

    App 2.0         a resposta usa <video> com um arquivo de videos/
    YouTube antigo  a resposta ainda tem o iframe do YouTube
    Sem vídeo       a resposta não tem vídeo nenhum

O painel fica em https://claude.ai/artifact/GUiia85VxYktwoEru7qp6b e não se
atualiza sozinho: depois de rodar aqui, troque o arquivo no menu Fontes da
própria página. Quem abre o painel consegue baixar essa planilha.
"""
import csv
import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / 'conteudo' / 'perguntas.html'
INDEX = RAIZ / 'index.html'
SAIDA = RAIZ / 'tools' / 'perguntas-video.csv'

APP, VELHO, NADA = 'App 2.0', 'YouTube antigo', 'Sem vídeo'


def situacao(corpo):
    """Como está o vídeo desta pergunta, e qual arquivo ela usa."""
    novo = re.search(r'src="\.\./videos/([^"]+\.mp4)"', corpo)
    if novo:
        return APP, novo.group(1)
    if 'youtube' in corpo:
        return VELHO, ''
    return NADA, ''


def main():
    fonte = FONTE.read_text(encoding='utf-8')
    # o rótulo bonito de cada categoria mora nos botões de filtro do index
    categorias = dict(re.findall(
        r'<button type="button" class="cp-chip" data-cat="([^"]+)"[^>]*>(.*?)</button>',
        INDEX.read_text(encoding='utf-8')))

    blocos = re.findall(r'<details id="([^"]+)" data-categoria="([^"]*)"(.*?)</details>',
                        fonte, re.S)
    if not blocos:
        sys.exit(f'Nenhuma pergunta encontrada em {FONTE.relative_to(RAIZ)}')

    linhas = []
    for numero, (_, cat, corpo) in enumerate(blocos, 1):
        titulo = re.search(r'faq-q__titulo">(.*?)</span>', corpo)
        titulo = html.unescape(re.sub(r'<[^>]+>', '', titulo.group(1))) if titulo else ''
        sit, arquivo = situacao(corpo)
        linhas.append([numero, titulo, categorias.get(cat, cat), sit, arquivo])

    with SAIDA.open('w', newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        escritor.writerow(['numero', 'pergunta', 'categoria', 'situacao', 'arquivo'])
        escritor.writerows(linhas)

    conta = {s: sum(1 for l in linhas if l[3] == s) for s in (APP, VELHO, NADA)}
    print(f'{len(linhas)} perguntas -> {SAIDA.relative_to(RAIZ)}')
    for rotulo in (APP, VELHO, NADA):
        print(f'  {conta[rotulo]:2}  {rotulo}')


if __name__ == '__main__':
    main()
