(() => {
  // Script legacy desativado: modal atual usa outro fluxo/ids.
  return;

  function fechar() {
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  function montarConteudo(data) {
    const limiteAtual = data.limite_atual_max
      ? `${data.limite_atual_min} a ${data.limite_atual_max} kg`
      : `${data.limite_atual_min || 0} kg ou mais`;
    const limiteNovo = data.limite_novo_max
      ? `${data.limite_novo_min} a ${data.limite_novo_max} kg`
      : `${data.limite_novo_min || 0} kg ou mais`;

    const categoriaAtualLabel = data.categoria_encontrada || data.categoria_atual || '-';
    const categoriaNovaLabel = data.categoria_nova || 'Não disponível';

    conteudo.innerHTML = `
      <p><strong>Atleta:</strong> ${data.atleta_nome || '-'}</p>
      <p><strong>Peso registrado:</strong> ${data.peso} kg</p>
      <hr style="margin: var(--spacing-3) 0;">
      <p><strong>Categoria atual:</strong><br>${categoriaAtualLabel}<br><small style="color: var(--color-gray-600);">(${limiteAtual})</small></p>
      <p><strong>Categoria sugerida:</strong><br>${categoriaNovaLabel}<br><small style="color: var(--color-gray-600);">(${limiteNovo})</small></p>
      <div style="margin-top: var(--spacing-3); background: var(--color-warning-light); padding: var(--spacing-3); border-radius: var(--border-radius-md);">
        <strong>Escolha:</strong> Remanejar (perde 1 ponto) ou Desclassificar (fora do evento).
      </div>
    `;
  }

  function bindModalActions(data, confirmUrl) {
    if (!formModal) return;
    formModal.action = confirmUrl;
    document.getElementById('modal-peso-oficial').value = data.peso || '';
    document.getElementById('modal-categoria-nova').value = data.categoria_nova || '';

    // Reset listeners
    btnDesclassificar?.replaceWith(btnDesclassificar.cloneNode(true));
    btnRemanejar?.replaceWith(btnRemanejar.cloneNode(true));
    const btnDesc = document.getElementById('modal-btn-desclassificar');
    const btnRem = document.getElementById('modal-btn-remanejar');

    btnDesc?.addEventListener('click', () => {
      const formData = new FormData(formModal);
      formData.append('acao', 'desclassificar');
      fetch(formModal.action, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(res => {
          if (res.success) {
            window.location.reload();
          } else {
            alert(res.message || 'Erro ao desclassificar.');
          }
        });
    });

    btnRem?.addEventListener('click', () => {
      const formData = new FormData(formModal);
      formData.append('acao', 'remanejar');
      fetch(formModal.action, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(res => {
          if (res.success) {
            window.location.reload();
          } else {
            alert(res.message || 'Erro ao remanejar.');
          }
        });
    });
  }

  function mostrar(data) {
    if (!modal || !conteudo || !formModal) return;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function abrirModal(data, confirmUrl) {
    montarConteudo(data);
    bindModalActions(data, confirmUrl);
    mostrar(data);
  }

  window.pesagemModal = { abrir: abrirModal, fechar };

  function handleFormSubmit(form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn?.textContent;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Salvando...';
      }

      const confirmUrl =
        form.dataset.confirmUrl ||
        (form.dataset.confirmUrlTemplate
          ? form.dataset.confirmUrlTemplate.replace('/0/', `/${form.dataset.inscricaoId || ''}/`)
          : '');

      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.categoria_ok) {
            window.location.reload();
            return;
          }

          if (data.success && data.precisa_confirmacao) {
            const finalConfirmUrl = data.confirm_url || confirmUrl || form.action;
            window.pesagemModal.abrir(data, finalConfirmUrl);
            submitBtn && ((submitBtn.disabled = false), (submitBtn.textContent = originalText));
            return;
          }

          alert(data.message || 'Erro ao registrar peso.');
          window.location.reload();
        })
        .catch(() => window.location.reload());
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('.js-form-pesagem');
    forms.forEach(handleFormSubmit);

    // Fechar modal ao clicar no overlay
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) fechar();
    });
    const modalContent = modal?.querySelector('.modal');
    modalContent?.addEventListener('click', (e) => e.stopPropagation());
  });
})();

