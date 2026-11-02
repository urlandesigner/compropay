# Roteiro: Como consultar o saldo de seus Cartões Comprocard?

Página da Wiki: `ComproPay Wiki/perguntas/como-consultar-o-saldo-de-seus-cartoes-comprocard.html`
Figma: App ComproPay 2, seção "Cartão" (7276:88645)

Fluxo curto: a aba Cartões já mostra o saldo dentro de cada cartão, sem
precisar abrir nada. São dois passos, não cinco.

| # | Tela (Figma) | Ação animada | Narração / legenda |
|---|---|---|---|
| 1 | v1 — Início (7276:90344) | toque em "Cartões" na barra de baixo | Na tela inicial, toque em **Cartões**, na barra de baixo. |
| 2 | Cartões (7276:88804) | os dois saldos acendem | O saldo de cada cartão aparece direto nele. |
| 3 | Cartões | "Principal" e "Bloqueado" acendem | Você também vê qual é o principal e se algum está bloqueado. Pronto! |

Duração estimada: 13 a 16 segundos.

## Por que destaque e não toque

Nos passos 2 e 3 nada é tocado: a informação já está na tela. Em vez do
círculo de toque que os outros vídeos usam, aqui um contorno acende em volta
do que a narração está falando. Toque fingido num lugar que não é botão
ensina errado.

## Telas da seção que ficam de fora

A seção "Cartão" tem o fluxo inteiro de adicionar cartão (formulário, escolha
da arte, confirmação) e a tela de gerenciar. Essas são de outras perguntas —
o cadastro já tem vídeo, em `video-cartao/`.

## Atenção: a tela tem 896 de altura, não 932

As telas desta seção foram desenhadas num quadro menor que as de "Favoritar"
e "Extrato". O `build.py` daqui usa `SH = 896`, e o recorte da tela inicial
acompanha. Copiar o build de outro vídeo sem ajustar isso corta o rodapé.
