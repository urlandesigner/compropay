# ComproPay Wiki

Ajuda, FAQ e tutoriais sobre o app e os sistemas da ComproPay. HTML puro + o design system em `DS wiki/`. Sem build e sem dependências.

```
./serve.sh          # http://localhost:3000
```

## Estrutura

```
index.html               a página inicial: título e busca, filtro de categorias, lista, rodapé
conteudo/perguntas.html  fonte das respostas (edite aqui)
perguntas/               uma página por pergunta (gerada)
tools/gerar-perguntas.py gerador das páginas e da lista
assets/site.css          cola com o DS (só layout, só tokens --cp-*)
assets/faq.js            filtro por categoria e busca (?categoria=slug&q=texto)
assets/ajuda.js          "Isso ajudou?" e WhatsApp
assets/config.js         número do WhatsApp
DS wiki/            design system: tokens, fonte Satoshi, componentes cp-*
```

**Nova pergunta:** copie um bloco `<details data-categoria="...">` de `conteudo/perguntas.html` e rode o gerador (abaixo).
O `data-categoria` tem de ser um dos `data-cat` dos botões do filtro.

Se mudar o DS, rode `./build.sh` dentro de `DS wiki/` para regenerar `dist/`.

## Perguntas

Cada pergunta tem uma página própria em `perguntas/`, e a lista do `index.html` leva para elas. As respostas moram em `conteudo/perguntas.html`. Depois de editar, incluir ou tirar uma resposta lá, rode:

```bash
python3 tools/gerar-perguntas.py
```

O gerador refaz `perguntas/` e a lista do `index.html`. Não edite esses dois à mão (a lista fica entre `LISTA:INICIO` e `LISTA:FIM`).

- **Passos e vídeo:** parágrafos `1- texto`, `2- texto`… viram a lista numerada. O vídeo (`.faq-video`) escreva no fim de cada seção, depois dos passos: o gerador o leva para logo antes da lista que ele ilustra.
- **Links nas respostas:** escreva `<a href="...">` simples; o estilo (roxo do DS, sublinhado) vem de `.pergunta__corpo a` em `assets/site.css`. Link para outra pergunta: só o nome do arquivo, `como-retirar-dinheiro-da-carteira-digital.html`.
- **WhatsApp:** o número fica em `assets/config.js`. Vazio = botão desativado.
- **Atualizado em:** `data-atualizado="2026-10-28"` no `<details>` da pergunta, depois rode o gerador.
- **Atualizadas recentemente:** aparece sozinha no `index.html` quando alguma pergunta tem `data-atualizado` (as 5 mais novas). Sem data nenhuma, a seção some.
- **Lista curta:** sem filtro nem busca, a home mostra as 8 primeiras perguntas e o botão "Ver todas" abre o resto (`LIMITE`, em `assets/faq.js`). Sem JavaScript a lista vem inteira.
- **Mais buscados:** `data-mais-buscada="1"` (ou 2, 3) no `<details>` põe a pergunta num dos 3 cards sob a busca da home e, nas páginas de categoria com uma pergunta só, no "Veja também". **Atalho:** Ctrl+K (⌘K no Mac) leva o cursor à busca.
- **404:** `404.html` da Wiki é gerado junto. O 404 da raiz do repositório leva para ele quando o endereço errado é de dentro de `ComproPay Wiki/`.
