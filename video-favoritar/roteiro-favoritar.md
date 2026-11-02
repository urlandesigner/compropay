# Roteiro: Como favoritar um estabelecimento?

Página da Wiki: `ComproPay Wiki/perguntas/como-favoritar-um-estabelecimento.html`
Figma: App ComproPay 2, seção "Favoritar" (7276:89590)

Mesmo formato do piloto: sem abertura, começa direto na tela inicial, telas do
app 2.0, narração e legenda. Cada linha é uma frase da narração e a legenda
correspondente.

| # | Tela (Figma) | Ação animada | Narração / legenda |
|---|---|---|---|
| 1 | v1 — Início (7276:89822) | toque no "+ Novo" de Favoritos | Na tela inicial, em **Favoritos**, toque em **Novo**. |
| 2 | Favoritar (7276:89593) | lista "Próximos de mim" entra | Você vê os estabelecimentos mais próximos de você. |
| 3 | Favoritar | toque na busca, "Subway" aparece | Ou busque pelo nome. |
| 4 | Resultado (7276:90138) | toque no marcador do item | Toque no marcador do estabelecimento. |
| 5 | Sheet (7276:90114) | sheet sobe, toque em "Favoritar" | Confirme em **Favoritar**. |
| 6 | Meus favoritos (7276:89731) | marcador fica roxo, troca de tela | Pronto! Ele já aparece em **Meus favoritos**. |

Duração estimada: 20 a 25 segundos.

## Telas montadas pelo script

Duas telas do vídeo não existem prontas no Figma e são montadas em `build.py`
com pixels das que existem:

- **Busca digitada**: a tela 7276:89593 com o campo de busca de 7276:90138
  colado por cima, para a palavra "Subway" aparecer sem trocar de tela.
- **Resultado ainda não favoritado**: a tela 7276:90138 com o marcador vazio da
  primeira linha colado sobre a segunda, que no Figma já vem favoritada. É o
  estado de "antes do toque".
