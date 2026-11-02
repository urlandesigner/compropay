# Vídeo: Como cadastrar um Cartão Comprocard?

Entra na pergunta `como-cadastrar-um-cartao-comprocard` da Wiki, no lugar do
vídeo do YouTube que mostrava o app antigo.

- `roteiro-cadastrar-cartao.md`: frases da narração e telas usadas
- `fig/`: telas exportadas da seção "Cartão" do Figma (App ComproPay 2), 1x
- `build.py`: monta o vídeo e a legenda `.vtt`

Para rodar, veja `../video-comum/README.md` — é de lá que vêm a fonte, o
modelo de voz e o Python. A saída vai para `out/`.

```
../video-comum/.venv/bin/python build.py
```

Depois, copie para a Wiki:

```
cp out/cadastrar-cartao.{mp4,jpg,vtt} "../ComproPay Wiki/videos/"
```

## Duas coisas que o Figma não dava de graça

**As telas do formulário saem com 414 de largura, as outras com 430.** O
`build.py` completa a diferença repetindo a coluna de cada borda, que é do
mesmo cinza de fundo. Esticar a tela deformaria o texto.

**A tela de Cartões abre e fecha o vídeo igual.** Não existe no Figma uma
versão dela sem o cartão novo, então a última frase diz que o cartão entrou na
carteira e a tela não mostra mudança nenhuma. O `build.py` resolve pondo um
aro em volta do cartão de cima nos segundos finais.
