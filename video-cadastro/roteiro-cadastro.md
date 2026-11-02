# Roteiro: Como criar sua conta no app ComproPay?

Figma: App ComproPay 2, board `1512:27797`, faixa "Fluxo cadastro inicial".
Segue o ramo **SIM** do losango "Telefone do ES?": celular do Espírito Santo,
da primeira tela até "Bem-vindo ao ComproPay!" no pré-cadastro aprovado.

Fica de fora, de propósito:

- o ramo **NÃO** (região não disponível → solicitar acesso → motivos →
  solicitação enviada, aprovada ou não): é outra pergunta
- "Editar suas informações" e as variantes com erro (CPF inválido, e-mail
  inválido, código incorreto, senhas diferentes)
- a faixa "Fluxo completar cadastro" (selfie com documento, envio de documentos)

| # | Tela | Ação | Narração / legenda |
|---|---|---|---|
| 1 | Onboarding | toque em "Criar conta" | Abra o app e toque em Criar conta. |
| 2 | CPF | toque no campo, teclado, toque em "Continuar" | Informe o seu CPF e toque em Continuar. |
| 3 | Criar conta | campos aparecem preenchidos | Preencha nome, celular do Espírito Santo, e-mail, nascimento e apelido. |
| 4 | Criar conta | rola até o gênero, toque em "Continuar" | Escolha o gênero e toque em Continuar. |
| 5 | Confirme seus dados | rola, toque em "Confirmar" | Confira os dados e toque em Confirmar. |
| 6 | Verificação (e-mail) | e-mail aparece, toque em "Continuar" | Agora informe o seu e-mail e toque em Continuar. |
| 7 | Verificação (código do e-mail) | código aparece, toque em "Continuar" | Digite o código que chegou no seu e-mail. |
| 8 | Verificação (SMS) | código aparece, toque em "Continuar" | Depois, digite o código que chegou por SMS. |
| 9 | Criar senha | senha e confirmação, toque em "Continuar" | Crie uma senha de seis números e confirme. |
| 10 | Ambiente seguro | — | O app abre a câmera para confirmar que é você. |
| 11 | Câmera, depois "Processando dados" | — | Centralize o rosto na marcação. |
| 12 | Pré-cadastro aprovado | — | Pronto! Seu pré-cadastro foi aprovado. Bem-vindo ao ComproPay! |

Duração: 48,6 s.

## O que sai do que o Figma mostra, e pode mudar

- **"Celular do Espírito Santo"** vem da tela "Ainda não disponível na sua
  região", que diz que o app aceita só números do ES. É regra de produto lida
  numa tela de design: se mudar, a frase 3 fica errada e o vídeo precisa ser
  refeito.
- **O código aparece com 3 dígitos e o cursor** ("3 5 0 |", "4 5 0 |") nas duas
  telas de verificação, e o botão já está ativo. É o que o design mostra; a
  narração não diz quantos dígitos tem o código.

## O que não dá para confiar no Figma

Os nomes das camadas estão trocados. Duas telas de "Criar conta" se chamam
"Endereços cep-V2", e o título grande de uma delas é uma camada chamada
"Completar cadastro". Por isso as 18 telas foram escolhidas olhando o que cada
uma mostra, não o nome. Os ids ficam em `fig/` pela ordem do fluxo.

O fluxo foi lido pela posição das telas e pelas anotações do board ("Telefone
do ES?", "SIM", "NÃO"). As setas não foram seguidas uma a uma.

## A pergunta da Wiki que esse vídeo substitui

"Como se cadastrar no app ComproPay?" hoje descreve o app antigo: termos de uso,
endereço de residência, SMS no fim. No app novo não há termos nem endereço no
meio do caminho, e entram e-mail, senha e câmera. Se o vídeo subir sem
reescrever os passos, texto e vídeo mostram coisas diferentes na mesma página.
