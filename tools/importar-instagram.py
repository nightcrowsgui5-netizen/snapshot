#!/usr/bin/env python3
"""Importa um post do Instagram para a galeria "Projetos Selecionados".

Baixa a imagem de capa do post, guarda em images/ e insere o item na galeria
com o clique levando ao post no Instagram.

Uso:
    python3 tools/importar-instagram.py <url-do-post> <categoria> ["Título"]

Categorias: eventos, corporativo, comercial, socialmedia, fotografia

O endereço da imagem no Instagram expira em algumas horas, por isso a imagem
é sempre baixada e guardada no site — nunca apontamos para o Instagram.
"""
import html
import io
import os
import re
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA_BOT = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}

ROTULOS = {
    "eventos": ("work.cat_evento", "Evento"),
    "corporativo": ("work.cat_corporativo", "Corporativo"),
    "comercial": ("work.cat_comercial", "Comercial"),
    "socialmedia": ("work.cat_socialmedia", "Social Media"),
    "fotografia": ("work.cat_fotografia", "Fotografia"),
}


def buscar(url, headers=UA_BOT, binario=False):
    dados = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40).read()
    return dados if binario else dados.decode("utf-8", "ignore")


def meta(pagina, prop):
    m = re.search(re.escape(prop) + r'" content="([^"]*)"', pagina)
    return html.unescape(m.group(1)) if m else None


def codigo_do_post(url):
    m = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", url)
    if not m:
        sys.exit("Não reconheci o endereço. Esperado algo como instagram.com/p/XXXXXXX/")
    return m.group(1)


def otimizar(caminho, largura_max=1400):
    """Reduz e recomprime para não pesar na página. Nunca amplia."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("  aviso: Pillow não instalado, imagem salva sem otimizar")
        return
    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    if im.width > largura_max:
        im.thumbnail((largura_max, largura_max * 4), Image.LANCZOS)
    im.save(caminho, "JPEG", quality=84, optimize=True, progressive=True)
    return im.size


def item_html(arquivo, categoria, titulo, url_post):
    chave, rotulo = ROTULOS[categoria]
    return (
        '          <div class="col-md-4 gallery-item ftco-animate" data-cat="%s">\n'
        '            <div class="model img d-flex align-items-end" style="background-image: url(images/%s);">\n'
        '            	<a href="%s" target="_blank" rel="noopener" aria-label="Ver no Instagram" class="icon d-flex justify-content-center align-items-center">\n'
        '	    					<span class="icon-instagram"></span>\n'
        '	    				</a>\n'
        '            	<div class="desc w-100 px-4">\n'
        '	              <div class="text w-100 mb-3">\n'
        '	              	<span data-i18n="%s">%s</span>\n'
        '	              	<h2><a href="%s" target="_blank" rel="noopener">%s</a></h2>\n'
        '	              </div>\n'
        '              </div>\n'
        '            </div>\n'
        '          </div>\n'
    ) % (categoria, arquivo, url_post, chave, rotulo, url_post, html.escape(titulo))


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ROTULOS:
        sys.exit(__doc__)
    url_post, categoria = sys.argv[1].split("?")[0], sys.argv[2]
    codigo = codigo_do_post(url_post)
    url_post = "https://www.instagram.com/p/%s/" % codigo

    print("Lendo o post %s ..." % codigo)
    pagina = buscar(url_post)
    url_img = meta(pagina, "og:image")
    if not url_img:
        sys.exit("Não achei a imagem de capa. O post pode estar privado ou removido.")

    autor = (meta(pagina, "og:title") or "").split(" on Instagram")[0].strip()
    legenda = meta(pagina, "og:title") or ""
    m = re.search(r'"(.*)', legenda, re.S)
    legenda = (m.group(1) if m else legenda).strip().strip('"')

    if len(sys.argv) > 3:
        titulo = sys.argv[3]
    else:
        # legenda de Instagram costuma ser longa demais para caber no card:
        # corta na primeira frase e, se ainda for grande, na última palavra inteira
        titulo = re.split(r"[.\n#!?]", legenda)[0].strip() or "Trabalho"
        if len(titulo) > 40:
            titulo = titulo[:40].rsplit(" ", 1)[0] + "..."
        print('  título sugerido: "%s"  (passe o 3o argumento para escolher outro)' % titulo)

    arquivo = "ig-%s.jpg" % codigo
    destino = os.path.join(RAIZ, "images", arquivo)
    print("Baixando a imagem ...")
    with open(destino, "wb") as f:
        f.write(buscar(url_img, headers={"User-Agent": "Mozilla/5.0"}, binario=True))
    tamanho = otimizar(destino)
    kb = os.path.getsize(destino) / 1024
    print("  images/%s  %s  %.0f KB" % (arquivo, "x".join(map(str, tamanho or ())), kb))
    if tamanho and min(tamanho) < 800:
        print("  ATENÇÃO: %dx%d é pequeno para a galeria. O Instagram só libera a\n"
              "  miniatura de compartilhamento publicamente. Para ficar nítido,\n"
              "  substitua images/%s pelo arquivo original." % (tamanho[0], tamanho[1], arquivo))

    caminho_html = os.path.join(RAIZ, "index.html")
    s = io.open(caminho_html, encoding="utf-8").read()
    if arquivo in s:
        sys.exit("Esse post já está na galeria (images/%s)." % arquivo)

    fim_galeria = "        </div>\n      </div>\n"
    i = s.index('<div class="row no-gutters">')
    j = s.index(fim_galeria, i)
    s = s[:j] + item_html(arquivo, categoria, titulo, url_post) + s[j:]
    io.open(caminho_html, "w", encoding="utf-8").write(s)

    print('\nPronto. Item "%s" adicionado à aba %s.' % (titulo, ROTULOS[categoria][1]))
    print("Autor do post: %s" % (autor or "?"))


if __name__ == "__main__":
    main()
