/* Filtro por categoria + busca que perdoa erro de digitação.
   Sem JavaScript a página mostra todas as perguntas.
   Estado na URL (?categoria=slug&q=texto), para o link ser compartilhável. */
(function () {
  var chips = document.querySelectorAll('.category-filter [data-cat]');
  var itens = Array.prototype.slice.call(document.querySelectorAll('#faq-lista li[data-categoria]'));
  var vazio = document.getElementById('faq-vazio');
  var contador = document.getElementById('faq-contador');
  var campo = document.getElementById('faq-busca');
  var novidades = document.getElementById('faq-novidades');
  var maisBuscados = document.getElementById('faq-mais-buscados');
  var lista = document.getElementById('faq-lista');
  var maisCaixa = document.getElementById('faq-mais-caixa');
  var mais = document.getElementById('faq-mais');
  var LIMITE = 8; // sem filtro nem busca, a lista mostra só as primeiras; "Ver todas" abre o resto
  var expandida = false;
  var estado = { cat: '', q: '' };

  // sem acento e sem caixa: "seguranca" acha "Segurança"
  function norma(s) { return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim(); }
  function palavras(s) { return norma(s).match(/[a-z0-9]+/g) || []; }

  // distância de edição (quantas letras trocar, tirar, pôr ou inverter de lugar: "senah" -> "senha" = 1)
  function distancia(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var ant2 = null, ant = [], i, j;
    for (j = 0; j <= b.length; j++) ant[j] = j;
    for (i = 1; i <= a.length; i++) {
      var atual = [i], menor = i;
      for (j = 1; j <= b.length; j++) {
        atual[j] = Math.min(ant[j] + 1, atual[j - 1] + 1, ant[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (ant2 && i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) atual[j] = Math.min(atual[j], ant2[j - 2] + 1);
        if (atual[j] < menor) menor = atual[j];
      }
      if (menor > max) return max + 1;
      ant2 = ant; ant = atual;
    }
    return ant[b.length];
  }

  // a palavra do texto casa com o que a pessoa digitou? Começo igual, ou até 1 erro (2 em palavras longas).
  function casa(termo, palavra) {
    if (palavra.indexOf(termo) === 0) return true;
    if (termo.length < 4) return false;
    var max = termo.length >= 8 ? 2 : 1;
    return distancia(termo, palavra, max) <= max || distancia(termo, palavra.slice(0, termo.length), max) <= max;
  }

  var dados = itens.map(function (el) {
    var t = el.querySelector('.faq-q__titulo');
    return { el: el, titulo: t, original: t.textContent, palavras: palavras(el.getAttribute('data-busca') || el.textContent) };
  });

  function combina(d, termos) {
    return termos.every(function (t) { return d.palavras.some(function (p) { return casa(t, p); }); });
  }

  // destaca no título as palavras que casaram (nós de texto + <mark>, sem innerHTML)
  function destacar(d, termos) {
    var t = d.titulo;
    while (t.firstChild) t.removeChild(t.firstChild);
    if (!termos.length) { t.textContent = d.original; return; }
    var re = /[A-Za-zÀ-ÖØ-öø-ÿ0-9]+/g, fim = 0, m;
    while ((m = re.exec(d.original))) {
      var p = norma(m[0]);
      if (!termos.some(function (x) { return casa(x, p); })) continue;
      if (m.index > fim) t.appendChild(document.createTextNode(d.original.slice(fim, m.index)));
      var mark = document.createElement('mark');
      mark.textContent = m[0];
      t.appendChild(mark);
      fim = m.index + m[0].length;
    }
    if (fim < d.original.length) t.appendChild(document.createTextNode(d.original.slice(fim)));
  }

  function rotulo(lista, attr, valor) {
    var c = Array.prototype.filter.call(lista, function (b) { return b.getAttribute(attr) === valor; })[0];
    return c ? c.textContent.trim() : '';
  }

  function aplicar(atualizarUrl) {
    var termos = palavras(estado.q), achou = 0, escondidas = 0;
    var filtrando = !!(estado.cat || termos.length);
    var recolher = !filtrando && !expandida;
    dados.forEach(function (d) {
      var casou = (!estado.cat || d.el.getAttribute('data-categoria') === estado.cat) && combina(d, termos);
      if (casou) achou++;
      var mostra = casou && !(recolher && achou > LIMITE);
      if (casou && !mostra) escondidas++;
      d.el.hidden = !mostra;
      if (mostra) destacar(d, termos);
    });
    chips.forEach(function (c) {
      c.setAttribute('aria-pressed', String((c.getAttribute('data-cat') || '') === estado.cat));
    });
    vazio.hidden = achou > 0;
    if (!achou) document.getElementById('faq-vazio-termo').textContent = estado.q.trim() ? '“' + estado.q.trim() + '”' : 'esta categoria';
    if (novidades) novidades.hidden = filtrando || !novidades.querySelector('li');
    // os 3 cards da home somem enquanto há busca ou categoria: o resultado é que importa
    if (maisBuscados) maisBuscados.hidden = filtrando || !maisBuscados.querySelector('li');
    // o selo de categoria só informa quando a lista mistura categorias
    lista.classList.toggle('sem-selo', !!estado.cat);
    // "Ver todas" só aparece com a lista curta
    if (maisCaixa) {
      maisCaixa.hidden = !escondidas;
      mais.textContent = 'Ver todas as ' + achou + ' perguntas';
    }
    // o contador só diz algo quando há filtro ou busca
    var txt = achou + (achou === 1 ? ' pergunta' : ' perguntas');
    if (estado.cat) txt += ' em ' + rotulo(chips, 'data-cat', estado.cat);
    if (estado.q.trim()) txt += ' para “' + estado.q.trim() + '”';
    contador.textContent = filtrando && achou ? txt : '';
    contador.hidden = !contador.textContent;
    if (atualizarUrl) {
      var p = new URLSearchParams();
      if (estado.cat) p.set('categoria', estado.cat);
      if (estado.q.trim()) p.set('q', estado.q.trim());
      history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
    }
  }

  // "Ver todas": as perguntas novas entram animadas (a classe liga a animação do CSS só aqui),
  // o foco vai para a primeira delas e o leitor de tela ouve o que mudou.
  if (mais) mais.addEventListener('click', function () {
    var antes = dados.filter(function (d) { return !d.el.hidden; });
    expandida = true;
    lista.classList.add('faq-expandindo');
    aplicar(false);
    var novas = dados.filter(function (d) { return !d.el.hidden && antes.indexOf(d) < 0; });
    novas.forEach(function (d, i) { d.el.style.transitionDelay = Math.min(i, 6) * 30 + 'ms'; });
    if (novas[0]) novas[0].el.querySelector('a').focus();
    var anuncio = document.getElementById('faq-anuncio');
    if (anuncio) anuncio.textContent = 'Mostrando todas as ' + (antes.length + novas.length) + ' perguntas.';
    setTimeout(function () {
      lista.classList.remove('faq-expandindo');
      novas.forEach(function (d) { d.el.style.transitionDelay = ''; });
    }, 700);
  });

  chips.forEach(function (c) {
    c.addEventListener('click', function () { estado.cat = c.getAttribute('data-cat') || ''; aplicar(true); });
  });
  campo.addEventListener('input', function () { estado.q = campo.value; aplicar(true); });

  // Atalho: Ctrl+K (⌘K no Mac) leva o cursor para a busca.
  var mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  var dica = document.querySelector('#faq-atalho kbd');
  if (dica && mac) dica.textContent = '⌘';
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      campo.focus();
      campo.select();
    }
  });

  var params = new URLSearchParams(location.search);
  var cat = params.get('categoria') || '';
  var valida = Array.prototype.some.call(chips, function (c) { return c.getAttribute('data-cat') === cat; });
  estado.cat = valida ? cat : '';
  estado.q = params.get('q') || '';
  campo.value = estado.q;
  aplicar(false);

  // Link antigo com #id: leva direto para a página da pergunta.
  var alvo = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (alvo && alvo.matches('#faq-lista li')) location.replace('perguntas/' + alvo.id + '.html');
})();
