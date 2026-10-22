(()=>{'use strict';
const SUPPORTED=['de','es','en','fr','nl','ru'];
const cache=new Map();
let currentRequest=0;
const mapping=[['legal','legal'],['privacy','privacy'],['cookies','cookies']];
const tr=(lang,key)=>window.FYHOM_TRANSLATIONS?.[lang]?.[key]||window.FYHOM_TRANSLATIONS?.de?.[key]||key;
function updateHeading(section,title,body){
  const wrapper=document.createElement('section');wrapper.className='fy-legal-topic';
  const h=document.createElement('h2');h.textContent=title;wrapper.append(h);
  const p=document.createElement('p');p.textContent=body;wrapper.append(p);
  section.append(wrapper);
}
function clearSection(element,msg){
  element.replaceChildren();
  const text=document.createElement('p');text.className='fy-legal-loading';text.textContent=msg;element.append(text);
}
async function getLegalData(lang){
  if(cache.has(lang))return cache.get(lang);
  const response=await fetch('/content/legal/'+encodeURIComponent(lang)+'.json',{cache:'no-store'});
  if(!response.ok)throw Error('Legal policy data HTTP '+response.status);
  const data=await response.json();
  if(!data||data.lang!==lang||!mapping.every(([kind])=>Array.isArray(data[kind])&&data[kind].length>0))throw Error('Incomplete policy translation '+lang);
  cache.set(lang,data);return data;
}
async function render(lang){
  lang=SUPPORTED.includes(lang)?lang:'es';
  const turn=++currentRequest;
  const sections=mapping.map(([type])=>({type,element:document.getElementById('fy-'+type+'-content')}));
  for(const {element} of sections)if(element)clearSection(element,tr(lang,'legalPageLoading'));
  try{
    const data=await getLegalData(lang);
    if(turn!==currentRequest)return;
    for(const {type,element} of sections){
      if(!element)continue;
      element.replaceChildren();
      for(const item of data[type]){
        if(typeof item?.title!=='string'||typeof item?.body!=='string')continue;
        updateHeading(element,item.title,item.body);
      }
    }
  }catch(error){
    console.warn('FYHOM legal pages unavailable:',error);
    if(turn!==currentRequest)return;
    for(const {element} of sections)if(element)clearSection(element,tr(lang,'legalPageError')+' info@fyhom.es');
  }
}
window.FYHOM_RENDER_LEGAL=render;
render(localStorage.getItem('fyhom-lang')||'es');
})();