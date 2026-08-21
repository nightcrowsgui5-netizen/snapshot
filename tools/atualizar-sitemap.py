#!/usr/bin/env python3
"""Regera o sitemap.xml a partir do index.html.

Declara cada imagem da galeria (para o Google Imagens) e atualiza a data de
modificação. Rodar sempre que a galeria mudar — o script de importação já
chama este automaticamente.

Uso:
    python3 tools/atualizar-sitemap.py
"""
import datetime
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.pollymaker.com.br/"


def escapar(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def imagens_da_galeria(html_txt):
    """(caminho, título) de cada item, na ordem em que aparecem."""
    itens = []
    for m in re.finditer(r'<img class="model-img" src="(images/[^"]+)" alt="([^"]*)"', html_txt):
        caminho, alt = m.group(1), m.group(2)
        # o alt é "Título — Categoria | PollyMaker, Tuparetama-PE"
        titulo = alt.split(" | ")[0].replace("&mdash;", "—").replace("&amp;", "&")
        itens.append((caminho, titulo))
    return itens


def main():
    html_txt = io.open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    itens = imagens_da_galeria(html_txt)
    if not itens:
        sys.exit("Não achei imagens da galeria em index.html — nada foi escrito.")

    hoje = datetime.date.today().isoformat()
    bloco = "".join(
        "    <image:image>\n"
        "      <image:loc>%s%s</image:loc>\n"
        "      <image:title>%s</image:title>\n"
        "    </image:image>\n" % (BASE, caminho, escapar(titulo))
        for caminho, titulo in itens
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        "  <url>\n"
        "    <loc>%s</loc>\n"
        "    <lastmod>%s</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        "    <priority>1.0</priority>\n" % (BASE, hoje)
        + bloco +
        "  </url>\n</urlset>\n"
    )
    io.open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    print("sitemap.xml: %d imagens declaradas, lastmod %s" % (len(itens), hoje))


if __name__ == "__main__":
    main()
