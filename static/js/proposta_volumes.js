document.addEventListener('DOMContentLoaded', function () {
  const radioTipo = document.querySelectorAll('input[name="tipo_simulacao"]');
  const secVolumes = document.getElementById('simulacao-volumes-section');
  const secManual = document.getElementById('simulacao-manual-section');

  // if sections missing, bail out
  if (!secVolumes || !secManual) return;

  // Toggle function
  function toggleTipo(tipo) {
    if (tipo === 'manual') {
      secVolumes.style.display = 'none';
      secManual.style.display = 'block';
    } else {
      secVolumes.style.display = 'block';
      secManual.style.display = 'none';
    }
  }

  radioTipo.forEach(r => {
    r.addEventListener('change', (e) => toggleTipo(e.target.value));
  });

  // default: respect checked radio
  const checked = document.querySelector('input[name="tipo_simulacao"]:checked');
  toggleTipo(checked ? checked.value : 'volumes');

  // ==============================
  // AUTO PREENCHER PESO TOTAL (MANUAL)
  // ==============================
  const manualTextarea = secManual.querySelector('textarea[name="simulacao_texto"]');
  const pesoTotalInput = secManual.querySelector('input[name="peso_total_kg"]');

  function parseNumberBR(raw) {
    if (!raw) return null;
    const s = String(raw)
      .replace(/\s+/g, '')
      .replace(/\.(?=\d{3}(?:\D|$))/g, '') // remove separador de milhar
      .replace(',', '.');
    const v = Number.parseFloat(s);
    return Number.isFinite(v) ? v : null;
  }

  function findPesoFromText(text) {
    const t = (text || '').toString();

    // 1) Preferência: '=peso 52,18' / 'peso=52,18' / 'peso: 52,18'
    const mEq = t.match(/(?:^|\b)(?:=\s*peso|peso\s*[:=])\s*([0-9]+(?:[\.,][0-9]+)?)(?:\s*kg\b)?/i);
    if (mEq && mEq[1]) {
      const v = parseNumberBR(mEq[1]);
      if (v != null) return { value: v, kind: 'explicit' };
    }

    // 2) Preferência: total entre parênteses '(52,18kg)'
    let lastParen = null;
    const reParen = /\(\s*([0-9]+(?:[\.,][0-9]+)?)\s*kg\s*\)/ig;
    let m;
    while ((m = reParen.exec(t)) !== null) {
      lastParen = m[1];
    }
    if (lastParen) {
      const v = parseNumberBR(lastParen);
      if (v != null) return { value: v, kind: 'explicit' };
    }

    // 3) Fallback: soma todos os pesos encontrados '17,34kg'
    const reKg = /([0-9]+(?:[\.,][0-9]+)?)\s*kg\b/ig;
    let sum = 0;
    let found = 0;
    while ((m = reKg.exec(t)) !== null) {
      const v = parseNumberBR(m[1]);
      if (v != null) {
        sum += v;
        found += 1;
      }
    }
    if (found > 0) return { value: sum, kind: 'sum' };

    return null;
  }

  function setPesoTotalFromManualText() {
    if (!manualTextarea || !pesoTotalInput) return;
    const res = findPesoFromText(manualTextarea.value);
    if (!res) return;

    const rounded = Math.round(res.value * 100) / 100;
    const formatted = rounded.toFixed(2);

    // Não sobrescreve se o usuário digitou manualmente (a menos que seja um valor auto-preenchido antes)
    const wasAuto = pesoTotalInput.dataset.autofill === '1';
    const current = pesoTotalInput.value;
    if (current && !wasAuto) return;

    pesoTotalInput.value = formatted;
    pesoTotalInput.dataset.autofill = '1';
  }

  if (pesoTotalInput) {
    pesoTotalInput.addEventListener('input', () => {
      // Usuário editou manualmente: não sobrescreve mais automaticamente.
      pesoTotalInput.dataset.autofill = '0';
    });
  }

  if (manualTextarea) {
    let pesoTimer;
    const schedule = () => {
      window.clearTimeout(pesoTimer);
      pesoTimer = window.setTimeout(setPesoTotalFromManualText, 200);
    };
    manualTextarea.addEventListener('input', schedule);
    manualTextarea.addEventListener('blur', setPesoTotalFromManualText);
    // inicializa ao carregar
    setPesoTotalFromManualText();
  }

  // Volumes list logic (only if exists)
  const volumesList = document.getElementById('volumes-list');
  const addBtn = document.getElementById('add-volume');

  if (!volumesList || !addBtn) return;

  function updateIndexes() {
    const items = volumesList.querySelectorAll('.volume-item');
    items.forEach((it, idx) => {
      it.querySelector('.volume-header').textContent = 'Volume ' + (idx + 1);
      // update names
      const select = it.querySelector('.select-caixa');
      select.name = `volume_select[${idx}]`;
      const qtd = it.querySelector('input[name^="volume_qtd"]');
      if (qtd) qtd.name = `volume_qtd[${idx}]`;
      const peso = it.querySelector('input[name^="volume_peso"]');
      if (peso) peso.name = `volume_peso[${idx}]`;
      const manual = it.querySelector('.volume-manual');
      if (manual) {
        manual.querySelectorAll('input').forEach(inp => {
          const field = inp.getAttribute('placeholder') || inp.name;
          if (inp.placeholder && inp.placeholder.includes('Comprimento')) inp.name = `manual_volumes[${idx}][comprimento]`;
          if (inp.placeholder && inp.placeholder.includes('Largura')) inp.name = `manual_volumes[${idx}][largura]`;
          if (inp.placeholder && inp.placeholder.includes('Altura')) inp.name = `manual_volumes[${idx}][altura]`;
          if (inp.placeholder && inp.placeholder.includes('Quantidade')) inp.name = `manual_volumes[${idx}][quantidade]`;
        });
      }
      const remove = it.querySelector('.remove-volume');
      if (remove) remove.style.display = (items.length > 1) ? 'inline-block' : 'none';
    });
  }

  function bindItem(it) {
    const select = it.querySelector('.select-caixa');
    const manualBlock = it.querySelector('.volume-manual');
    select.addEventListener('change', (e) => {
      if (e.target.value === 'manual') {
        manualBlock.style.display = 'block';
      } else {
        manualBlock.style.display = 'none';
      }
    });

    const remove = it.querySelector('.remove-volume');
    remove.addEventListener('click', () => {
      it.remove();
      updateIndexes();
    });
  }

  addBtn.addEventListener('click', () => {
    const count = volumesList.querySelectorAll('.volume-item').length;
    const template = volumesList.querySelector('.volume-item').outerHTML;
    volumesList.insertAdjacentHTML('beforeend', template);
    updateIndexes();
    const newItem = volumesList.querySelectorAll('.volume-item')[volumesList.querySelectorAll('.volume-item').length - 1];
    bindItem(newItem);
  });

  // bind existing
  volumesList.querySelectorAll('.volume-item').forEach(it => bindItem(it));
  updateIndexes();
});
