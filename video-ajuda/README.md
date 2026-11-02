# Vídeo: Como acessar a Central de Ajuda?

Entra na pergunta `como-acessar-a-central-de-ajuda` da Wiki, que nasceu junto
com ele: nenhuma das 27 perguntas anteriores falava de ajuda ou atendimento.

- `roteiro-central-de-ajuda.md`: frases da narração, telas e as medidas tiradas
  do Figma
- `fig/`: telas da seção "Ajuda" (App ComproPay 2), 1x
- `build.py`: monta o vídeo e a legenda `.vtt`

Para rodar, veja `../video-comum/README.md` — é de lá que vêm a fonte, o
modelo de voz e o Python. A saída vai para `out/`.

```
../video-comum/.venv/bin/python build.py
```

Depois, copie para a Wiki:

```
cp out/central-de-ajuda.{mp4,jpg,vtt} "../ComproPay Wiki/videos/"
```

## Mistura os dois formatos

Toque onde o usuário precisa tocar (o item "Ajuda" do menu, o banner da Lia) e
holofote onde é só para mostrar o que a tela tem (busca, banner, lista de
contatos). A pergunta é "onde fica e o que tem dentro", então um formato só não
dava conta.

## A tela do chat se chama outra coisa no Figma

O frame é `7287:99764`, "Pessoa física - passo 3 email-V2". O conteúdo é o chat
com a Lia; o nome ficou de outro fluxo.
