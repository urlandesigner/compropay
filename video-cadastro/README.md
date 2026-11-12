# Vídeo: Como criar sua conta no app ComproPay?

Entra na pergunta `como-se-cadastrar-no-app-compropay` da Wiki, no lugar do
vídeo do YouTube do app antigo. **Ainda não entrou:** o arquivo está pronto em
`out/`, e o texto escrito da pergunta precisa ser reescrito junto.

- `roteiro-cadastro.md`: frases da narração, o ramo que o vídeo segue e o que
  ficou de fora
- `fig/`: as telas do vídeo, 1x, numeradas pela ordem do fluxo. As duas primeiras
  (`01-entrada-vazia`, `02-entrada-cpf`) são capturas reais do app no iPhone; as
  outras vêm do board `1512:27797` (App ComproPay 2). O CPF aparece borrado em
  todas elas
- `preparar-telas-reais.py`: gera as duas telas reais a partir de
  `capturas-iphone/cadastro/` (fora do Git), borrando o CPF
- `build.py`: monta o vídeo e a legenda `.vtt`

Para rodar, veja `../video-comum/README.md`:

```
../video-comum/.venv/bin/python build.py
```

Depois, copie para a Wiki:

```
cp out/cadastro.{mp4,jpg,vtt} "../ComproPay Wiki/videos/"
```

## As telas de 1091 de altura

O formulário "Criar conta" e "Confirme seus dados" são frames de 414x1091, mais
altos que o aparelho (896). O `build.py` mostra cada um por uma janela de 896:
o cabeçalho e o botão ficam fixos e o meio rola 195 px. As outras 15 telas
entram como estão, sem redimensionar.
