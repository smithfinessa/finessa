(() => {
  const drawer = document.getElementById('finessaDrawer');
  const launch = document.getElementById('finessaLaunch');
  const close = document.getElementById('finessaClose');
  const chat = document.getElementById('finessaChat');
  const form = document.getElementById('finessaForm');
  const input = document.getElementById('finessaInput');
  const token = document.getElementById('csrfToken');

  function openDrawer(){ if(!drawer) return; drawer.classList.add('open'); drawer.setAttribute('aria-hidden','false'); setTimeout(()=>input?.focus(),120); }
  function closeDrawer(){ if(!drawer) return; drawer.classList.remove('open'); drawer.setAttribute('aria-hidden','true'); }
  launch?.addEventListener('click', openDrawer); close?.addEventListener('click', closeDrawer);

  function escapeHtml(value){ return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
  function messageHtml(role, text){ return `<article class="message ${role}"><div class="bubble"><p>${escapeHtml(text)}</p></div></article>`; }
  function resultHtml(data){
    let html = `<article class="message assistant"><div class="bubble"><p>${escapeHtml(data.answer || 'I could not produce a response.')}</p>`;
    if(data.authorities?.length){
      html += `<div class="authority-results"><strong>Research leads</strong>`;
      data.authorities.forEach(a => { html += `<div class="authority-hit"><span>${escapeHtml(a.jurisdiction_code || '')}</span><b>${escapeHtml(a.title || '')}</b><small>${escapeHtml(a.citation || '')}</small></div>`; });
      html += `</div>`;
    }
    if(data.actions?.length){ html += `<div class="assistant-actions">${data.actions.map(a=>`<a href="${escapeHtml(a.href)}">${escapeHtml(a.label)}</a>`).join('')}</div>`; }
    if(data.notice){ html += `<small class="assistant-notice">${escapeHtml(data.notice)}</small>`; }
    return html + `</div></article>`;
  }
  function currentCaseId(){
    const m = location.pathname.match(/\/cases\/(\d+)/);
    return m ? m[1] : null;
  }

  async function ask(targetChat, text, csrf){
    targetChat.insertAdjacentHTML('beforeend', messageHtml('user', text));
    const wait = document.createElement('article'); wait.className='message assistant thinking'; wait.innerHTML='<div class="bubble"><span></span><span></span><span></span></div>'; targetChat.appendChild(wait); targetChat.scrollTop=targetChat.scrollHeight;
    try{
      const res = await fetch('/api/finessa/chat', {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf || ''}, body:JSON.stringify({message:text, case_id:currentCaseId()})});
      const data = await res.json(); wait.remove(); targetChat.insertAdjacentHTML('beforeend', resultHtml(data));
    }catch(e){ wait.remove(); targetChat.insertAdjacentHTML('beforeend', messageHtml('assistant','I could not reach the Justice Gateway assistant service. Please try again.')); }
    targetChat.scrollTop=targetChat.scrollHeight;
  }
  form?.addEventListener('submit', e => { e.preventDefault(); const text=input.value.trim(); if(!text) return; input.value=''; ask(chat,text,token?.value); });
  document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click', () => { openDrawer(); if(input){ input.value=btn.dataset.prompt; form?.requestSubmit(); } }));

  const pageChat=document.getElementById('assistantPageChat');
  const pageForm=document.getElementById('assistantPageForm');
  const pageInput=document.getElementById('assistantPageInput');
  const pageToken=document.getElementById('assistantPageCsrf');
  pageForm?.addEventListener('submit',e=>{e.preventDefault();const text=pageInput.value.trim();if(!text)return;pageInput.value='';ask(pageChat,text,pageToken?.value);});
  document.querySelectorAll('.assistant-prompt').forEach(btn=>btn.addEventListener('click',()=>{if(pageInput){pageInput.value=btn.dataset.prompt;pageForm?.requestSubmit();}}));
})();
