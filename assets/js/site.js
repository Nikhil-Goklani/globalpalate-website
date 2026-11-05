(function(){
'use strict';
var D=document,B=D.body,ROOT=B.getAttribute('data-root')||'';
var HTTP=/^https?:$/.test(location.protocol);
function meta(n){var m=D.querySelector('meta[name="'+n+'"]');return m?m.content:''}
function $(s,c){return (c||D).querySelector(s)}function $$(s,c){return [].slice.call((c||D).querySelectorAll(s))}
var PHONE=B.getAttribute('data-phone')||'+1 323 784 9803',EMAIL=B.getAttribute('data-email')||'sales@globalpalate.co';

var CV=B.getAttribute('data-conv');if(CV){try{window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:'gp_lead_confirmed',lead_type:CV})}catch(e){}}
/* announcement bar */
var bar=$('.bar');
if(bar){
 try{if(sessionStorage.getItem('gp-bar')==='1')bar.hidden=true}catch(e){}
 var pb=$('.bar-pause',bar),cb=$('.bar-close',bar);
 if(pb)pb.addEventListener('click',function(){var p=bar.classList.toggle('paused');pb.setAttribute('aria-pressed',p);pb.textContent=p?'Play':'Pause'});
 if(cb)cb.addEventListener('click',function(){bar.hidden=true;try{sessionStorage.setItem('gp-bar','1')}catch(e){}});
}
/* mobile nav */
var bg=$('.burger'),nav=$('nav.primary');
if(bg&&nav)bg.addEventListener('click',function(){var o=nav.classList.toggle('open');bg.setAttribute('aria-expanded',o)});
/* tabs (product pages) */
$$('[role=tablist]:not(.tabs2)').forEach(function(tl){
 var tabs=$$('[role=tab]',tl);
 function sel(t){tabs.forEach(function(x){var on=x===t;x.setAttribute('aria-selected',on);x.tabIndex=on?0:-1;var p=D.getElementById(x.getAttribute('aria-controls'));if(p)p.hidden=!on});}
 tabs.forEach(function(t,i){t.addEventListener('click',function(){sel(t)});t.addEventListener('keydown',function(e){var n=null;if(e.key==='ArrowRight')n=tabs[(i+1)%tabs.length];if(e.key==='ArrowLeft')n=tabs[(i+tabs.length-1)%tabs.length];if(n){e.preventDefault();sel(n);n.focus()}})});
});
/* Turnstile */
var TS=meta('gp-turnstile'),tsLoaded=false;
function loadTs(){if(!TS||tsLoaded)return;tsLoaded=true;var s=D.createElement('script');s.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';s.async=true;s.onload=function(){$$('.ts').forEach(renderTs)};D.head.appendChild(s)}
function renderTs(el){if(!TS||!window.turnstile||el.getAttribute('data-r'))return;el.setAttribute('data-r','1');window.turnstile.render(el,{sitekey:TS,theme:'light'})}
$$('.ts').forEach(function(el){if(TS)loadTs()});

/* lead submit */
function ep(){return HTTP?'/api/lead':ROOT+'api/lead'}
function thanks(t){return HTTP?'/thank-you/'+t+'/':ROOT+'thank-you/'+t+'/index.html'}
function collect(form){
 var o={products:[]};
 $$('input,select,textarea',form).forEach(function(f){
  if(!f.name)return;
  if(f.type==='checkbox'){if(f.checked){if(f.name==='products')o.products.push(f.value);else o[f.name]=f.value}return}
  if(f.type==='radio'){if(f.checked)o[f.name]=f.value;return}
  if(f.name==='products'){if(f.value)o.products.push(f.value);return}
  o[f.name]=f.value;
 });
 o.page=location.pathname;o.rendered=form.getAttribute('data-t')||'';
 return o;
}
function showErr(form,msg){var e=$('.err',form);if(!e){e=D.createElement('div');e.className='err';e.setAttribute('role','alert');form.insertBefore(e,form.firstChild)}e.hidden=false;e.textContent=msg}
function submitLead(form){
 var type=form.getAttribute('data-lead');var data=collect(form);
 if(data.req_type&&type!=='inquiry')type=data.req_type;
 if(form.getAttribute('data-force'))type=form.getAttribute('data-force');
 data.type=type;
 var btns=$$('button[type=submit]',form);btns.forEach(function(b){b.disabled=true});
 var fail='We could not send your request. Please call '+PHONE+' or email '+EMAIL+' and we will help right away.';
 return fetch(ep(),{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(data)})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok&&j.ok,j:j}})})
  .then(function(x){
    if(x.ok){try{window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:'gp_lead',lead_type:type})}catch(e){}location.href=thanks(type)}
    else{btns.forEach(function(b){b.disabled=false});showErr(form,(x.j&&x.j.error)?x.j.error+' ('+PHONE+')':fail)}})
  .catch(function(){btns.forEach(function(b){b.disabled=false});showErr(form,fail)});
}
D.addEventListener('submit',function(e){var f=e.target;if(!f.matches||!f.matches('form[data-lead]'))return;e.preventDefault();if(f.hasAttribute('data-multistep')&&!f.classList.contains('final'))return;submitLead(f)});
$$('form[data-lead]').forEach(function(f){f.setAttribute('data-t',Date.now())});

/* modal */
var dlg=null;
var PRODUCTS=[];try{PRODUCTS=JSON.parse(B.getAttribute('data-products')||'[]')}catch(e){}
function build(){
 dlg=D.createElement('dialog');dlg.className='gpm';dlg.setAttribute('aria-labelledby','gpm-t');
 var checks=PRODUCTS.map(function(p){return '<label><input type="checkbox" name="products" value="'+p[0]+'"> '+p[1]+'</label>'}).join('');
 var tsd=TS?'<div class="ts"></div>':'';
 dlg.innerHTML='<div class="gpm-g"><div class="gpm-l"><span class="kicker">Contact us</span><h2 id="gpm-t">Let&rsquo;s talk about your order</h2><p>Tell us what you need and our team will reply '+(B.getAttribute('data-response')||'within one business day')+'.</p><p>Prefer to talk now? Call <a href="tel:'+PHONE.replace(/[^+\d]/g,'')+'"><strong>'+PHONE+'</strong></a>, '+(B.getAttribute('data-hours')||'')+'.</p></div>'
 +'<div class="gpm-r"><button type="button" class="gpm-x" aria-label="Close dialog">Close &#10005;</button>'
 +'<div class="tabs2" role="tablist" aria-label="Request type"><button type="button" role="tab" id="gt1" aria-selected="true" aria-controls="gp1">Get a quote</button><button type="button" role="tab" id="gt2" aria-selected="false" aria-controls="gp2" tabindex="-1">General inquiry</button></div>'
 +'<div id="gp1" role="tabpanel" aria-labelledby="gt1"><div class="steps" aria-hidden="true"><span class="on" data-s="1">1 Your details</span><span data-s="2">2 Product details</span></div>'
 +'<form class="form" data-lead="quote" data-multistep="1" novalidate>'
 +'<div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>'
 +'<div class="stp on" data-p="1"><div class="r2"><div><label class="req" for="m-fn">First name</label><input id="m-fn" name="first_name" autocomplete="given-name" required></div><div><label class="req" for="m-ln">Last name</label><input id="m-ln" name="last_name" autocomplete="family-name" required></div></div>'
 +'<div class="r2"><div><label class="req" for="m-em">Work email</label><input id="m-em" name="email" type="email" autocomplete="email" required></div><div><label class="req" for="m-co">Company</label><input id="m-co" name="company" autocomplete="organization" required></div></div>'
 +'<div class="r2"><div><label for="m-ph">Phone (optional)</label><input id="m-ph" name="phone" type="tel" autocomplete="tel"></div><div><label for="m-url">Company website (optional)</label><input id="m-url" name="company_url" placeholder="www.yourcompany.com"></div></div>'
 +'<div class="acts"><button type="button" class="btn btn-dark" data-next>Next: product details</button></div></div>'
 +'<div class="stp" data-p="2"><div class="radios" role="radiogroup" aria-label="Request type"><label><input type="radio" name="req_type" value="quote" checked> Request a quote</label><label><input type="radio" name="req_type" value="sample"> Request a sample</label></div>'
 +'<fieldset style="border:0;padding:0;margin:0"><legend class="sr">Products of interest</legend><label style="margin-bottom:6px">Products of interest</label><div class="checks">'+checks+'</div></fieldset>'
 +'<div class="r2"><div><label class="req" for="m-q">Quantity needed</label><div style="display:grid;grid-template-columns:1fr 90px;gap:8px"><input id="m-q" name="quantity" type="number" min="1" step="any" required><select name="unit" aria-label="Unit"><option value="kg">kg</option><option value="drum">drums</option></select></div></div><div><label class="req" for="m-z">Delivery ZIP / postal code</label><input id="m-z" name="zip" autocomplete="postal-code" required></div></div>'
 +'<div class="r2"><div><label for="m-d">Needed by</label><input id="m-d" name="needed_by" type="date"></div><div><label class="req" for="m-u">Intended use</label><select id="m-u" name="intended_use" required><option value="">Select&hellip;</option><option>Dietary supplement</option><option>Functional food &amp; beverage</option><option>Herbal / traditional formulation</option><option>Spice &amp; seasoning</option><option>Other</option></select></div></div>'
 +'<label for="m-n">Notes (specs, certifications, documents needed)</label><textarea id="m-n" name="message" rows="3"></textarea>'+tsd
 +'<div class="acts"><button type="button" class="btn" data-back>Back</button><button type="submit" class="btn btn-dark">Send request</button></div></div>'
 +'</form></div>'
 +'<div id="gp2" role="tabpanel" aria-labelledby="gt2" hidden><form class="form" data-lead="inquiry"><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>'
 +'<div class="r2"><div><label class="req" for="i-n">Full name</label><input id="i-n" name="first_name" required></div><div><label class="req" for="i-e">Work email</label><input id="i-e" name="email" type="email" required></div></div>'
 +'<label for="i-c">Company</label><input id="i-c" name="company"><label class="req" for="i-m">Message</label><textarea id="i-m" name="message" rows="4" required></textarea>'+tsd
 +'<div class="acts"><button type="submit" class="btn btn-dark">Send message</button></div></form></div>'
 +'</div></div>';
 B.appendChild(dlg);
 $('.gpm-x',dlg).addEventListener('click',function(){dlg.close()});
 dlg.addEventListener('click',function(e){if(e.target===dlg)dlg.close()});
 var t1=$('#gt1',dlg),t2=$('#gt2',dlg);
 function tab(a){var q=a===1;t1.setAttribute('aria-selected',q);t2.setAttribute('aria-selected',!q);t1.tabIndex=q?0:-1;t2.tabIndex=q?-1:0;$('#gp1',dlg).hidden=!q;$('#gp2',dlg).hidden=q}
 t1.addEventListener('click',function(){tab(1)});t2.addEventListener('click',function(){tab(2)});
 $$('[role=tab]',dlg).forEach(function(t){t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){tab(2);t2.focus()}if(e.key==='ArrowLeft'){tab(1);t1.focus()}})});
 var qf=$('form[data-lead=quote]',dlg);
 function step(n){$$('.stp',qf).forEach(function(s){s.classList.toggle('on',s.getAttribute('data-p')==n)});$$('.steps span',dlg).forEach(function(s){s.classList.toggle('on',s.getAttribute('data-s')<=n)});var f=$('.stp.on input,.stp.on select',qf);if(f)f.focus()}
 $('[data-next]',qf).addEventListener('click',function(){var ok=true;$$('.stp[data-p="1"] [required]',qf).forEach(function(f){if(!f.checkValidity()){if(ok)f.reportValidity();ok=false}});if(ok)step(2)});
 $('[data-back]',qf).addEventListener('click',function(){step(1)});
 qf.addEventListener('submit',function(e){if($('.stp.on',qf).getAttribute('data-p')==='1'){e.stopImmediatePropagation();e.preventDefault();$('[data-next]',qf).click();return}var ok=true;$$('.stp[data-p="2"] [required]',qf).forEach(function(f){if(!f.checkValidity()){if(ok)f.reportValidity();ok=false}});if(!ok){e.stopImmediatePropagation();e.preventDefault();return}qf.classList.add('final')},true);
 $$('form[data-lead]',dlg).forEach(function(f){f.setAttribute('data-t',Date.now())});
 dlg._tab=tab;dlg._step=step;
 $$('.ts',dlg).forEach(function(el){if(TS){loadTs();renderTs(el)}});
}
function openModal(opts){
 if(!window.HTMLDialogElement){location.href=ROOT+'contact/index.html#quote';return}
 if(!dlg)build();
 dlg._tab(1);dlg._step(1);
 var qf=$('form[data-lead=quote]',dlg);qf.classList.remove('final');
 var rq=$('input[name=req_type][value=quote]',dlg);if(rq)rq.checked=true;$$('input[name=products]',dlg).forEach(function(c){c.checked=false});
 if(opts.sample){var r=$('input[name=req_type][value=sample]',dlg);if(r)r.checked=true}
 if(opts.product){var c=$('input[name=products][value='+opts.product+']',dlg);if(c)c.checked=true}
 dlg.showModal();
}
D.addEventListener('click',function(e){var t=e.target.closest&&e.target.closest('[data-quote]');if(!t)return;e.preventDefault();openModal({sample:t.getAttribute('data-quote')==='sample',product:t.getAttribute('data-product')})});

/* analytics (only if configured, after consent) */
var GA=meta('gp-ga4');
if(GA){
 var ck=$('.cookie');var choice=null;try{choice=localStorage.getItem('gp-consent')}catch(e){}
 function ga(){var s=D.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+GA;D.head.appendChild(s);window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config',GA)}
 if(choice==='yes')ga();else if(!choice&&ck){ck.hidden=false}
 if(ck){$('[data-yes]',ck).addEventListener('click',function(){try{localStorage.setItem('gp-consent','yes')}catch(e){}ck.hidden=true;ga()});$('[data-no]',ck).addEventListener('click',function(){try{localStorage.setItem('gp-consent','no')}catch(e){}ck.hidden=true})}
}
})();
