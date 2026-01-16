document.addEventListener("DOMContentLoaded", () => {
  console.log("✓ proposta_detail.js carregado");
  
  const steps = document.querySelectorAll(".step");
  console.log("✓ Steps encontrados:", steps.length);

  const sections = {
    "sec-simulacao": document.getElementById("sec-simulacao"),
    "sec-cotacao": document.getElementById("sec-cotacao"),
    "sec-envio": document.getElementById("sec-envio")
  };
  
  console.log("✓ Seções encontradas:", Object.keys(sections));

  function showSection(sectionId) {
    console.log("🎯 Mostrando seção:", sectionId);
    
    // Esconde todas as seções
    Object.entries(sections).forEach(([id, section]) => {
      if (section) {
        section.style.display = "none";
        console.log(`  → Ocultando ${id}`);
      }
    });

    // Mostra apenas a seção selecionada
    const section = sections[sectionId];
    if (section) {
      section.style.display = "block";
      console.log(`  → Mostrando ${sectionId}`);
    }
  }

  function setActive(step) {
    steps.forEach(s => s.classList.remove("active"));
    step.classList.add("active");
    console.log("✓ Step marcado como active:", step.dataset.target);
  }

  // Clique nos steps - comportamento de tabs
  steps.forEach((step, index) => {
    console.log(`  Adicionando listener ao step ${index}: ${step.dataset.target}`);
    
    step.addEventListener("click", (e) => {
      console.log("🖱️ Click no step:", step.dataset.target);
      e.preventDefault();
      e.stopPropagation();
      
      const sectionId = step.dataset.target;
      setActive(step);
      showSection(sectionId);
    });
  });

  // Impressão do preview
  const btnPrint = document.getElementById('btn-print');
  if (btnPrint) {
    btnPrint.addEventListener('click', () => {
      const preview = document.getElementById('proposal-preview');
      if (!preview) return;
      const w = window.open('', '_blank');
      w.document.write('<html><head><title>Proposta</title>');
      // include minimal styles
      const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
      styles.forEach(h => w.document.write(`<link rel="stylesheet" href="${h}">`));
      w.document.write('</head><body>');
      w.document.write(preview.innerHTML);
      w.document.write('</body></html>');
      w.document.close();
      w.print();
    });
  }
});

