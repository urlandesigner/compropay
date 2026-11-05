# Capturar telas do iPhone (sem montar vídeo)

Guarda a tela que está **agora** na janela do Espelhamento do iPhone como imagem.
Não monta vídeo. Quem navega no app é a pessoa; isto só tira o retrato.

```
video-comum/.venv/bin/python video-comum/capturar/capturar.py <fluxo> <nome> ["o que é esta tela"]
video-comum/.venv/bin/python video-comum/capturar/capturar.py --listar
```

Exemplo, três telas do fluxo da Rede:

```
capturar.py rede-credenciada lista "Lista aberta pelo atalho Rede"
capturar.py rede-credenciada busca "Campo de busca com o teclado"
capturar.py rede-credenciada loja "Detalhe de um estabelecimento"
```

## Onde fica

`capturas-iphone/<fluxo>/` na raiz do projeto:

- `NN-<nome>.png`: só a tela do aparelho, em **2x (~748x1626)**, PNG sem perda, cantos
  arredondados transparentes. `NN` conta sozinho.
- `janela/NN-<nome>.png`: a janela inteira, sem recorte, caso precise.
- `indice.md`: tabela em ordem (arquivo, o que é, tamanho, data).

**A pasta não vai para o Git** (`.git/info/exclude`). As telas do app real trazem nome,
saldo e final de cartão, e o repositório é público. O que vai para a Wiki é o vídeo, depois
da folha de revisão do montador.

## Como funciona

A janela é achada pelo sistema e capturada com `screencapture -l`, que entrega o dobro da
resolução que a captura por automação (391x860) e com fundo transparente fora do aparelho.
Não precisa de permissão extra além da Gravação de Tela que o Terminal/Claude já tem.

## Quando recusa

- **"Conexão Pausada":** o espelhamento pausa por inatividade. Clique em *Retomar* na
  janela. Se o iPhone estiver em uso, o Mac também mostra essa tela cinza.
- **Janela não encontrada:** abra o Espelhamento do iPhone e deixe a janela visível.
- `--forcar` salva mesmo assim (só se o app tiver uma tela escura lisa de verdade).

## Antes de usar uma captura num vídeo

Confira o que aparece: hora e bateria reais na barra de status, nome, saldo, notificação
no topo. O montador (`../montador/`) troca a barra por uma limpa e mostra a folha de revisão.
