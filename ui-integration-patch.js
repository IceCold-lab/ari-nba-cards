/* Ari NBA Cards — 2026 UI/data integration patch */
(() => {
  const PATCH_VERSION = '2026-09-26';

  function applyPortraitFrame() {
    const style = document.createElement('style');
    style.id = 'ari-portrait-patch';
    style.textContent = `
      .photo { width:100% !important; aspect-ratio:3 / 4 !important; height:auto !important; min-height:0 !important; overflow:hidden !important; }
      .photo img { width:100% !important; height:100% !important; object-fit:cover !important; display:block !important; }
    `;
    document.head.appendChild(style);
  }

  async function loadOverrides() {
    try { return await fetch('roster-overrides.json', {cache:'no-store'}).then(r=>r.ok?r.json():{}); }
    catch (_) { return {}; }
  }

  function mergeOverrides(data, overrides) {
    return data.map(p => {
      const o = overrides[p.id];
      if (!o) return p;
      return {...p, ...o};
    });
  }

  function installLearnModeGuard() {
    // This guard is deliberately narrow: it hides all answer information until reveal in Learn mode.
    const originalRender = window.render;
    if (typeof originalRender !== 'function') return;
    window.render = function() {
      originalRender.apply(this, arguments);
      if (window.mode === 'learn' && !window.revealed) {
        const hide = id => { const el=document.getElementById(id); if(el) el.innerHTML=''; };
        hide('team'); hide('number'); hide('facts'); hide('trophies'); hide('draft');
        const photo=document.getElementById('photo');
        if(photo){ photo.className='photo missing'; photo.textContent=''; }
      }
    };
  }

  window.ARI_PATCH_VERSION = PATCH_VERSION;

  // Apply after the existing application has booted. This keeps players.json as the
  // canonical dataset while layering current transaction corrections on top.
  loadOverrides().then(overrides => {
    if (window.DATA && Array.isArray(window.DATA)) {
      window.DATA = mergeOverrides(window.DATA, overrides);
      window.deck = [...window.DATA];
      if (typeof window.initTabs === 'function') window.initTabs();
      if (typeof window.render === 'function') window.render();
    }
    installLearnModeGuard();
  });
})();
