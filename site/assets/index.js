
(function(){
  const data = JSON.parse(document.getElementById('data').textContent);
  const grid = document.getElementById('grid'); const count = document.getElementById('count');
  const state = {type:'all', sport:'', county:'', remote:false, q:'', sort:'score'};
  function card(r){
    const cover = r.cover ? `style="background-image:url('${r.cover}')"` : '';
    const pct = r.pct ? `<span class="pct">${r.pct}%</span>` : '';
    return `<a class="card" href="p/${r.id}.html">
      <div class="cover" ${cover}>${pct}</div>
      <div class="body">
        <div class="tags"><span class="tag ${r.type==='運動員'?'t-ath':'t-team'}">${r.type}</span><span class="tag">${r.sport}</span>${r.remote?'<span class="tag t-remote">偏鄉</span>':''}</div>
        <h3>${r.name}</h3>
        <div class="meta">${r.county||''}${r.coach?' · 教練 '+r.coach:''}</div>
        <p class="ex">${r.excerpt||''}</p>
        <div class="foot"><div><small>需求金額</small><b class="num">${r.amount_text}</b></div><div class="flags">${r.flags.map(f=>`<span class="flag">${f.replace('需求','')}</span>`).join('')}</div></div>
        <div class="bar"><i style="width:${Math.min(100,r.pct)}%"></i></div>
      </div></a>`;
  }
  function apply(){
    let rows = data.filter(r => (state.type==='all'||r.type===state.type)
      && (!state.sport||r.sport===state.sport) && (!state.county||r.county===state.county)
      && (!state.remote||r.remote) && (!state.q||(r.name+r.sport+r.county+r.tagline+r.excerpt+(r.coach||'')).toLowerCase().includes(state.q)));
    const s = state.sort;
    rows.sort((a,b)=> s==='amount_desc'?b.amount-a.amount : s==='amount_asc'?a.amount-b.amount : s==='name'?a.name.localeCompare(b.name,'zh-Hant') : s==='updated'?(b.updated||'').localeCompare(a.updated||'') : b.score-a.score);
    grid.innerHTML = rows.length ? rows.map(card).join('') : '<div class="empty">找不到符合條件的計畫，試試放寬篩選。</div>';
    count.textContent = `顯示 ${rows.length} / ${data.length} 個計畫`;
    document.querySelectorAll('.seg button').forEach(b=>b.classList.toggle('on', b.dataset.type===state.type));
  }
  document.querySelectorAll('.seg button').forEach(b=>b.addEventListener('click',()=>{state.type=b.dataset.type;apply();}));
  document.getElementById('sport').addEventListener('change',e=>{state.sport=e.target.value;apply();});
  document.getElementById('county').addEventListener('change',e=>{state.county=e.target.value;apply();});
  document.getElementById('remote').addEventListener('change',e=>{state.remote=e.target.checked;apply();});
  document.getElementById('sort').addEventListener('change',e=>{state.sort=e.target.value;apply();});
  document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value.trim().toLowerCase();apply();});
  document.querySelectorAll('.chip[data-sport]').forEach(c=>c.addEventListener('click',()=>{state.sport=c.dataset.sport;document.getElementById('sport').value=state.sport;apply();document.getElementById('browse').scrollIntoView({behavior:'smooth'});}));
  apply();
})();
