/* Partes comuns da central de ajuda (página inicial e páginas de perguntas):
   "Isso ajudou?" e canal de WhatsApp.
   Cada página de pergunta tem um elemento [data-faq-item] com id. Config em assets/config.js. */
(function () {
  var cfg = window.AJUDA_CONFIG || {};
  var numero = String(cfg.whatsapp || '').replace(/\D/g, '');

  function ligarWhatsApp(a) {
    if (numero) {
      a.href = 'https://wa.me/' + numero + (cfg.mensagem ? '?text=' + encodeURIComponent(cfg.mensagem) : '');
      a.target = '_blank'; a.rel = 'noopener';
      a.removeAttribute('aria-disabled');
    } else {
      a.removeAttribute('href'); a.removeAttribute('target');
      a.setAttribute('aria-disabled', 'true');
    }
  }

  // Voltar: se a pessoa veio de outra página da Wiki, volta nela (a lista mantém busca e categoria);
  // se abriu a pergunta direto por um link, o href leva à página inicial.
  Array.prototype.forEach.call(document.querySelectorAll('[data-voltar]'), function (a) {
    a.addEventListener('click', function (e) {
      if (history.length > 1 && document.referrer.indexOf(location.origin) === 0) { e.preventDefault(); history.back(); }
    });
  });

  // "Isso ajudou?": guarda só neste navegador; o evento faq:feedback fica pronto para ligar numa métrica.
  var guardado = {};
  try { guardado = JSON.parse(localStorage.getItem('cp-wiki-feedback') || '{}'); } catch (e) {}
  function salvar() { try { localStorage.setItem('cp-wiki-feedback', JSON.stringify(guardado)); } catch (e) {} }

  Array.prototype.forEach.call(document.querySelectorAll('[data-faq-item]'), function (el) {
    var corpo = el.querySelector('.pergunta__corpo');
    if (!corpo) return;

    var caixa = document.createElement('div');
    caixa.className = 'faq-feedback';
    corpo.appendChild(caixa);

    function mostrarPergunta() {
      caixa.textContent = '';
      var rot = document.createElement('span');
      rot.className = 'faq-feedback__rotulo';
      rot.textContent = 'Isso ajudou?';
      caixa.appendChild(rot);
      [['sim', 'Sim'], ['nao', 'Não']].forEach(function (op) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'cp-btn cp-btn--secondary cp-btn--sm';
        b.textContent = op[1];
        b.addEventListener('click', function () {
          guardado[el.id] = op[0]; salvar();
          document.dispatchEvent(new CustomEvent('faq:feedback', { detail: { id: el.id, ajudou: op[0] === 'sim' } }));
          mostrarResposta(op[0]);
        });
        caixa.appendChild(b);
      });
    }
    function mostrarResposta(v) {
      caixa.textContent = '';
      var msg = document.createElement('span');
      msg.className = 'faq-feedback__rotulo faq-feedback__msg';
      msg.setAttribute('role', 'status');
      msg.textContent = v === 'sim' ? 'Que bom! Obrigado pelo retorno.' : 'Obrigado por avisar. Vamos melhorar esta resposta.';
      caixa.appendChild(msg);
      if (v === 'nao') {
        var a = document.createElement('a');
        a.className = 'cp-link';
        a.textContent = 'Falar com a equipe';
        ligarWhatsApp(a);
        caixa.appendChild(a);
      }
      var troca = document.createElement('button');
      troca.type = 'button';
      troca.className = 'cp-link faq-feedback__troca';
      troca.textContent = 'Mudar resposta';
      troca.addEventListener('click', function () { delete guardado[el.id]; salvar(); mostrarPergunta(); });
      caixa.appendChild(troca);
    }
    if (guardado[el.id]) mostrarResposta(guardado[el.id]); else mostrarPergunta();
  });

  // Vídeo: a caixa cinza dá lugar ao player com fade. O prazo de 4 s garante que ele nunca fique escondido.
  Array.prototype.forEach.call(document.querySelectorAll('.faq-video'), function (caixa) {
    var f = caixa.querySelector('iframe');
    if (!f) return;
    caixa.classList.add('faq-video--espera');
    var pronto = function () { caixa.classList.remove('faq-video--espera'); };
    f.addEventListener('load', pronto);
    setTimeout(pronto, 4000);
  });

  // Movimento: com "menos movimento" ligado no aparelho, nada disto roda e a página aparece inteira e parada.
  var semMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!semMovimento) {
    // A entrada em sequência da lista vale só na carga; depois sai, para o filtro não repeti-la a cada letra.
    var entrada = document.querySelector('.question-list.faq-entrada');
    if (entrada) setTimeout(function () { entrada.classList.remove('faq-entrada'); }, 1800);

    // Blocos abaixo da dobra aparecem quando entram na tela. Sem IntersectionObserver, ficam como estão.
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add('revelado');
          io.unobserve(e.target);
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
      Array.prototype.forEach.call(document.querySelectorAll('.pergunta__relacionadas, .faq-suporte'), function (el) {
        el.classList.add('js-revelar');
        io.observe(el);
      });
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-whatsapp-link]'), ligarWhatsApp);
  var aviso = document.querySelector('[data-whatsapp-aviso]');
  if (aviso) aviso.hidden = !!numero;
})();
