# Roteiro: Como consultar a rede credenciada ComproPay e Comprocard?

Página da Wiki: `ComproPay Wiki/perguntas/como-consultar-a-rede-credenciada-compropay-e-comprocard.html`
Vídeo atual: Lhql5cSG03I (app antigo, YouTube)

Sem abertura. Começa na tela inicial, rola até Serviços, toca em Rede e cai na
lista de estabelecimentos. Depois da navegação, ninguém toca em mais nada: a
lista é só leitura, então o que mostra cada parte é o holofote (o resto escurece).

| # | Tela | Ação animada | Narração / legenda |
|---|---|---|---|
| 1 | Início (rolada até Serviços) | a tela rola; holofote nos Serviços | Na tela inicial, role até **Serviços**. |
| 2 | Início → Rede credenciada | toque no atalho "Rede" | Toque em **Rede**. |
| 3 | Rede credenciada | — | Aparece a lista dos estabelecimentos credenciados. |
| 4 | Rede credenciada | holofote na busca | No topo, busque por nome, cidade ou bairro. |
| 5 | Rede credenciada | holofote no primeiro estabelecimento | Em cada um, você pode ligar ou ver no mapa onde fica. |
| 6 | Rede credenciada | — | Pronto! É só escolher o estabelecimento. |

Duração estimada: 22 a 26 segundos.

## De onde vêm as telas

- **Início**: `fig/home.png`, a mesma do vídeo da tela inicial (frame `7276:89822`,
  App ComproPay 2).
- **Rede credenciada**: `fig/rede.png`, frame `0:10610` ("Rede credenciada-V2",
  página Produção do mesmo arquivo), 414x896.

## Atenção: a tela da Rede não está nas seções do 2.0

O Figma tem seções do 2.0 para Home, Cartão, Favoritar, Pagar, Extrato e Ajuda.
**Não tem uma da Rede.** A lista usada aqui é a "Rede credenciada-V2" da página
Produção — a mesma do fluxo "Rede credenciada" do Design System 1.0, com busca
"Buscar nome, cidade, bairro" e os atalhos Telefone, Ver no mapa e Pagar. Existe
uma segunda variante (`0:27165`), mais simples, sem busca nem Pagar; não foi usada.

**Confirmada pelo Urlan em 02/11/2026**: é essa a tela que vale para a Rede.

Se a Rede ganhar tela própria no 2.0, troque o `fig/rede.png` e confira as
medidas do holofote em `build.py` (`BUSCA` e `CARTAO1`).

## O que mudou no texto escrito

O passo 2 de hoje ("clique no segmento que deseja buscar") descreve o fluxo
antigo, com a escolha de segmento antes da lista. No fluxo descrito para o 2.0,
o atalho Rede abre a lista direto.
