
(function(){
  const links=[...document.querySelectorAll('.subnav a')]; const secs=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
  function spy(){ let cur=secs[0]; for(const s of secs){ if(s.getBoundingClientRect().top-140<=0) cur=s; } links.forEach(a=>a.classList.toggle('on', a.getAttribute('href')==='#'+cur.id)); }
  window.addEventListener('scroll',spy,{passive:true}); spy();
  const lb=document.getElementById('lb'), lbi=lb.querySelector('img');
  document.querySelectorAll('[data-full]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();lbi.src=a.dataset.full;lb.classList.add('on');}));
  lb.addEventListener('click',()=>lb.classList.remove('on'));
  const sh=document.getElementById('share'); if(sh) sh.addEventListener('click',()=>{ (navigator.clipboard?navigator.clipboard.writeText(location.href):Promise.reject()).then(()=>{sh.textContent='已複製連結 ✓';setTimeout(()=>sh.textContent='分享此頁',1800);}).catch(()=>prompt('複製此網址',location.href)); });
})();
