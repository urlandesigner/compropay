# Roteiro: a tela inicial

Figma: App ComproPay 2, frame `7276:89822` (v1, 430x1255)
Tela: `fig/home.png`, exportada 1x

Não é passo a passo: é um tour. Ninguém toca em nada. A tela rola e cada
seção acende enquanto o resto escurece.

## Seções, na ordem, com os limites medidos no frame

| # | Seção | y no frame | Rolagem | Narração / legenda |
|---|---|---|---|---|
| 1 | Header | 62–124 | 0 | No topo, seu perfil, os atalhos rápidos e os avisos. |
| 2 | Meus cartões | 124–306 | 0 | Logo abaixo, seus cartões, cada um com o saldo à vista. |
| 3 | Saldo na carteira | 330–465 | 0 | O saldo da carteira, com transferir, depositar e cobrar na mão. |
| 4 | Favoritos | 489–604 | 0 | Os estabelecimentos que você favoritou, e o atalho pra adicionar outros. |
| 5 | Vantagens para você | 640–827 | 80 | As ofertas e vantagens do momento. |
| 6 | Serviços | 863–1128 | 316 | E os atalhos dos serviços: rede, cashback, rotativo, boletos e o resto. |
| 7 | Menu inferior | 1155–1240 | 316 | No rodapé, o menu: Início, Extrato, Pagar, Cartões e Ajuda. |
| 8 | — | — | 316 | Essa é a tela inicial do ComproPay. |

Duração estimada: 28 a 32 segundos.

## Como a rolagem funciona

A tela do aparelho no vídeo tem 430x932, mas o frame tem 1255 de altura.
Então:

- barra de status (y 0–62) fica fixa no topo
- menu inferior (y 1155–1255) fica fixo no rodapé do aparelho
- o meio rola de 0 a 316, que é o quanto falta pra chegar no fim dos Serviços

## Duas decisões que eu tomei

1. **"Vantagens para você" entrou**, mesmo não estando na sua lista. Ela fica
   entre Favoritos e Serviços: se ficasse de fora, a tela rolaria por cima de
   uma seção inteira sem ninguém falar nada, e o vídeo pareceria quebrado.
2. **"Atalhos" virou "Serviços"**, que é o nome que está na tela — a grade de
   Rede, Cashback, Rotativo, Boletos, Vendas, Empréstimos, Doações e Ver todos.

## O que ainda não está decidido

Onde esse vídeo entra. Não existe pergunta na Wiki sobre a tela inicial; as 26
que existem são todas "como fazer X". Um tour da home é outro tipo de conteúdo.

## Por que não tem "nova" em lugar nenhum

A palavra "nova" saiu do rótulo e da última frase. A Wiki fica no ar por anos
e o `CLAUDE.md` do repositório pede texto que não precise de edição quando o
projeto crescer: daqui a um tempo "a nova tela inicial" vira mentira, e aí
alguém tem que achar e regravar o vídeo. "A tela inicial" continua certo.
