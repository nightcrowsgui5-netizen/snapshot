#!/usr/bin/env python3
"""Importa um post do Instagram para a galeria "Projetos Selecionados".

Baixa a imagem de capa do post, guarda em images/ e insere o item na galeria
com o clique levando ao post no Instagram.

Uso:
    python3 tools/importar-instagram.py <url-do-post> <categoria> ["Título"] [--girar=90] [--vertical]

--girar    gira a imagem em graus no sentido anti-horário. Use quando a capa
           do reel vier tombada (vídeo gravado na horizontal).
--vertical recorta uma imagem deitada no formato vertical da galeria, para não
           sobrar faixa preta. Aceita o ponto de corte: --vertical=700.

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


PROPORCAO_GALERIA = 480.0 / 600.0  # o espaço de cada item é 480x600


def recortar_vertical(im, deslocamento=None):
    """Recorta uma imagem deitada no formato vertical da galeria.

    Imagem deitada exibida inteira num espaço vertical sobra faixa preta em
    cima e embaixo e fica pequena. Aqui pegamos a altura toda e a maior
    largura possível na proporção do espaço.
    """
    largura = int(im.height * PROPORCAO_GALERIA)
    if largura >= im.width:
        return im  # já é vertical, nada a recortar
    x = (im.width - largura) // 2 if deslocamento is None else deslocamento
    x = max(0, min(x, im.width - largura))
    return im.crop((x, 0, x + largura, im.height))


def otimizar(caminho, largura_max=1400, girar=0, vertical=False, deslocamento=None):
    """Reduz e recomprime para não pesar na página. Nunca amplia.

    girar: graus no sentido anti-horário. Capas de reel gravado na horizontal
    costumam vir tombadas, porque a rotação fica nos metadados do vídeo e o
    Instagram não a aplica ao exportar o quadro.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("  aviso: Pillow não instalado, imagem salva sem otimizar")
        return
    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    if girar:
        im = im.rotate(girar, expand=True)
    if vertical:
        antes = im.size
        im = recortar_vertical(im, deslocamento)
        if im.size != antes:
            print("  recortada no vertical: %dx%d -> %dx%d" % (antes + im.size))
    if im.width > largura_max:
        im.thumbnail((largura_max, largura_max * 4), Image.LANCZOS)
    im.save(caminho, "JPEG", quality=84, optimize=True, progressive=True)
    return im.size


def fim_do_ultimo_item(s):
    """Posição logo após o último item da galeria.

    Procurar por um fecha-div solto não serve: a indentação varia e o item
    acaba inserido fora da grade (e quebra a linha). Aqui achamos o último
    item e contamos a abertura/fechamento de div até ele fechar de verdade.
    """
    i = s.rindex('<div class="col-md-4 gallery-item')
    profundidade, pos = 0, i
    while True:
        abre = s.find("<div", pos)
        fecha = s.find("</div>", pos)
        if fecha == -1:
            raise SystemExit("Não consegui achar o fim da galeria em index.html")
        if abre != -1 and abre < fecha:
            profundidade += 1
            pos = abre + 4
        else:
            profundidade -= 1
            pos = fecha + 6
            if profundidade == 0:
                # inclui o fim de linha, para o próximo item começar limpo
                return pos + 1 if s[pos:pos + 1] == "\n" else pos


def item_html(arquivo, categoria, titulo, url_post, inteira=True, tamanho=None):
    """Monta o item da galeria.

    A imagem entra como <img> de verdade, e não como fundo de CSS, porque o
    Google Imagens não indexa fundo de CSS. O alt descreve o trabalho.
    """
    chave, rotulo = ROTULOS[categoria]
    classe = "model img ig-inteira" if inteira else "model img"
    alt = "%s — %s | PollyMaker, Tuparetama-PE" % (titulo, rotulo)
    dims = ' width="%d" height="%d"' % tamanho if tamanho else ""
    return (
        '          <div class="col-md-4 gallery-item ftco-animate" data-cat="%s">\n'
        '            <div class="%s d-flex align-items-end">\n'
        '            	<img class="model-img" src="images/%s" alt="%s"%s loading="lazy" decoding="async">\n'
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
    ) % (categoria, classe, arquivo, html.escape(alt, quote=True), dims,
         url_post, chave, rotulo, url_post, html.escape(titulo))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    girar, vertical, deslocamento = 0, False, None
    for a in sys.argv[1:]:
        if a.startswith("--girar"):
            girar = int(a.split("=")[1]) if "=" in a else 90
        elif a.startswith("--vertical"):
            vertical = True
            if "=" in a:
                deslocamento = int(a.split("=")[1])
    if len(args) < 2 or args[1] not in ROTULOS:
        sys.exit(__doc__)
    url_post, categoria = args[0].split("?")[0], args[1]
    codigo = codigo_do_post(url_post)
    url_post = "https://www.instagram.com/p/%s/" % codigo

    print("Lendo o post %s ..." % codigo)
    pagina = buscar(url_post)

    # A imagem de og:image vem CORTADA em quadrado pelo Instagram. O endpoint
    # /media/?size=l entrega a imagem inteira e bem maior, então tentamos ele
    # primeiro e só caímos na miniatura se falhar.
    url_img = url_post + "media/?size=l"
    try:
        buscar(url_img, headers={"User-Agent": "Mozilla/5.0"}, binario=True)
        print("  usando a imagem inteira (/media/?size=l)")
    except Exception:
        url_img = meta(pagina, "og:image")
        print("  aviso: imagem inteira indisponível, usando a miniatura quadrada")
        if not url_img:
            sys.exit("Não achei a imagem. O post pode estar privado ou removido.")

    autor = (meta(pagina, "og:title") or "").split(" on Instagram")[0].strip()
    legenda = meta(pagina, "og:title") or ""
    m = re.search(r'"(.*)', legenda, re.S)
    legenda = (m.group(1) if m else legenda).strip().strip('"')

    if len(args) > 2:
        titulo = args[2]
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
    tamanho = otimizar(destino, girar=girar, vertical=vertical, deslocamento=deslocamento)
    kb = os.path.getsize(destino) / 1024
    print("  images/%s  %s  %.0f KB" % (arquivo, "x".join(map(str, tamanho or ())), kb))
    if tamanho:
        # o espaço da galeria tem 480x600 e a imagem é exibida inteira, então
        # o que importa não é a largura em si, e sim se ela precisa ser AMPLIADA
        # para caber (é a ampliação que borra). Em telas de alta densidade a
        # exibição dobra, por isso o fator 2.
        escala = min(480.0 / tamanho[0], 600.0 / tamanho[1]) * 2
        if escala > 1.5:
            print("  ATENÇÃO: %dx%d precisa ser ampliado %.1fx e vai ficar borrado.\n"
                  "  Substitua images/%s pelo arquivo original."
                  % (tamanho[0], tamanho[1], escala, arquivo))
        elif escala > 1.15:
            print("  ok: %dx%d serve bem. Em telas de alta densidade amplia %.2fx,\n"
                  "  perda leve. Se quiser o máximo de nitidez, use o arquivo original."
                  % (tamanho[0], tamanho[1], escala))
        else:
            print("  ok: %dx%d, resolução de sobra." % tamanho)

    caminho_html = os.path.join(RAIZ, "index.html")
    s = io.open(caminho_html, encoding="utf-8").read()
    if arquivo in s:
        sys.exit("Esse post já está na galeria (images/%s)." % arquivo)

    j = fim_do_ultimo_item(s)
    s = s[:j] + item_html(arquivo, categoria, titulo, url_post, tamanho=tamanho) + s[j:]
    io.open(caminho_html, "w", encoding="utf-8").write(s)

    print('\nPronto. Item "%s" adicionado à aba %s.' % (titulo, ROTULOS[categoria][1]))
    print("Autor do post: %s" % (autor or "?"))


if __name__ == "__main__":
    main()
