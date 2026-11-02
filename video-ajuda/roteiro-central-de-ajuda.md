# Roteiro: Como acessar a Central de Ajuda?

Pergunta nova na Wiki — não existe nenhuma sobre ajuda, suporte ou atendimento
entre as 27 que já estão lá.
Figma: App ComproPay 2, seção `7286:98936` ("Ajuda")

Começa na tela inicial. Mistura os dois formatos: toque onde o usuário precisa
tocar, holofote onde é só pra mostrar o que tem.

| # | Tela | Ação animada | Narração / legenda |
|---|---|---|---|
| 1 | Início | toque em "Ajuda" no menu de baixo | No menu de baixo do app, toque em **Ajuda**. |
| 2 | Central de Ajuda | — | A Central de Ajuda abre com tudo num lugar só. |
| 3 | Central de Ajuda | holofote na busca | Em cima, a busca: escreva sua dúvida. |
| 4 | Central de Ajuda | holofote no banner da Lia | Logo abaixo, a Lia, nossa atendente virtual. |
| 5 | Central de Ajuda | holofote na lista | E os atalhos: FAQ, telefones, ouvidoria e endereços. |
| 6 | Central de Ajuda | toque em "Fale com a Lia" | Toque em **Fale com a Lia** para abrir o chat. |
| 7 | Chat | — | Pronto, agora é só mandar sua mensagem. |

Duração estimada: 24 a 28 segundos.

## Medidas, tiradas do Figma

Na tela da Central de Ajuda (430x932):

| Parte | y |
|---|---|
| título "CENTRAL DE AJUDA" | 62–124 |
| campo de busca | 124–176 |
| banner "Fale com a Lia" | 211–351 |
| título "Opções de pagamento" | 386–410 |
| FAQ / Telefones / Ouvidoria / Endereços | 422–670 |
| menu inferior | 844–912 |

O menu inferior cai no mesmo lugar nas duas telas: na home ele fica em 1167–1235
do frame de 1255, que no vídeo vira 844–912. Então não há pulo na transição.

O botão "Ajuda" é o último dos cinco do menu, em x 330–406: o toque vai no
centro, (368, 878).

## Dois problemas no Figma que você vai querer ver

1. **O título "Opções de pagamento" está em cima da lista errada.** Embaixo dele
   vêm FAQ, Telefones, Ouvidoria e Endereços, que não são opções de pagamento.
   Parece sobra de copiar e colar de outra tela. A narração do vídeo chama a
   lista de "atalhos" e não lê esse título, mas ele aparece na imagem.
2. **A tela do chat se chama "Pessoa física - passo 3 email-V2"** no Figma. O
   conteúdo é o chat com a Lia; o nome ficou de outro fluxo.
