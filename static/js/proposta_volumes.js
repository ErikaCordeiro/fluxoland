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
