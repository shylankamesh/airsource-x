const study=[
  {title:'Next 0–24 hours',winner:'Persistence was better on this held-out horizon: MAE 26.64 µg/m³ versus 28.37 for LightGBM. Validation selected LightGBM before this test period; this test result is reported without retuning.',rows:[['LightGBM',28.3714,'ml'],['Persistence',26.6446,'persistence'],['Seasonal mean',39.8846,'seasonal']]},
  {title:'Following 24–48 hours',winner:'Persistence was selected using validation. On the held-out test, it reached MAE 38.98 µg/m³; LightGBM reached 34.53. Test results do not change the validation-time selection.',rows:[['LightGBM',34.5325,'ml'],['Persistence',38.9823,'persistence'],['Seasonal mean',42.034,'seasonal']]}
];
const chart=document.querySelector('#bar-chart');
const winner=document.querySelector('#winner-copy');
const title=document.querySelector('#horizon-title');
const tabs=[...document.querySelectorAll('.tab')];
function renderHorizon(index){
  const horizon=study[index];
  title.textContent=horizon.title;
  winner.textContent=horizon.winner;
  chart.replaceChildren(...horizon.rows.map(([name,value,type])=>{
    const row=document.createElement('div'); row.className='bar-row'; row.setAttribute('role','listitem');
    const label=document.createElement('span'); label.className='bar-name'; label.textContent=name;
    const track=document.createElement('div'); track.className='bar-track'; track.setAttribute('aria-hidden','true');
    const fill=document.createElement('div'); fill.className=`bar-fill ${type}`; fill.style.width=`${Math.min(value/45*100,100)}%`; track.append(fill);
    const number=document.createElement('span'); number.className='bar-value'; number.textContent=value.toFixed(2);
    row.append(label,track,number); return row;
  }));
  tabs.forEach((tab,i)=>{const active=i===index;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
  document.querySelector('#horizon-panel').setAttribute('aria-labelledby',tabs[index].id);
}
tabs.forEach((tab,index)=>{
  tab.addEventListener('click',()=>renderHorizon(index));
  tab.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();let next=index;
    if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;
    if(event.key==='ArrowRight')next=(index+1)%tabs.length;
    if(event.key==='Home')next=0;if(event.key==='End')next=tabs.length-1;
    tabs[next].focus();renderHorizon(next);
  });
});
renderHorizon(0);
