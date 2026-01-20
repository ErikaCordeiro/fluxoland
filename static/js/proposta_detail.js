document.addEventListener("DOMContentLoaded", () => {
  const steps = document.querySelectorAll(".step");
  const sections = {
    "sec-simulacao": document.getElementById("sec-simulacao"),
    "sec-cotacao": document.getElementById("sec-cotacao"),
    "sec-envio": document.getElementById("sec-envio")
  };

  function showSection(sectionId) {
    Object.entries(sections).forEach(([id, section]) => {
      if (section) section.style.display = "none";
    });

    const section = sections[sectionId];
    if (section) section.style.display = "block";

    const previewBox = document.getElementById("preview-box");
    if (previewBox) {
      previewBox.style.display = sectionId === "sec-envio" ? "none" : "block";
    }
  }

  function setActive(step) {
    steps.forEach(s => s.classList.remove("active"));
    step.classList.add("active");
  }

  steps.forEach((step) => {
    step.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      setActive(step);
      showSection(step.dataset.target);
    });
  });

  const btnPrint = document.getElementById('btn-print');
  if (btnPrint) {
    btnPrint.addEventListener('click', () => {
      const preview = document.getElementById('proposal-preview');
      if (!preview) return;
      const w = window.open('', '_blank');
      w.document.write('<html><head><title>Proposta</title>');
      const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
      styles.forEach(h => w.document.write(`<link rel="stylesheet" href="${h}">`));
      w.document.write('</head><body>');
      w.document.write(preview.innerHTML);
      w.document.write('</body></html>');
      w.document.close();
      w.print();
    });
  }

  const modalOverlay = document.querySelector('.modal-overlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        window.location.href = '/propostas';
      }
    });
  }

  const activeStep = document.querySelector('.step.active');
  if (activeStep && activeStep.dataset.target === 'sec-envio') {
    const previewBox = document.getElementById('preview-box');
    if (previewBox) previewBox.style.display = 'none';
  });

