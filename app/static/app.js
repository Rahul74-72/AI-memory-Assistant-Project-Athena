'use strict';
const $ = id => document.getElementById(id);
let token = '', profile = null, recorder = null, recordingTimer = null;
let lastCodeQuestion = '', lastCodeAnswer = '', photoURLs = [];
let installPrompt = null;
function notice(text, error=false) { $('notice').textContent=text; $('notice').className=error?'error':''; }
async function api(path, options={}) {
  const headers = {...options.headers};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {headers['Content-Type']='application/json'; options.body=JSON.stringify(options.body);}
  const response = await fetch(path, {...options, headers, credentials:'omit'});
  if (!response.ok) {
    const data = await response.json().catch(()=>({detail:'Request failed.'}));
    if(response.status===401 && !path.startsWith('/auth/login')) signedOut();
    throw new Error(typeof data.detail==='string'?data.detail:'Please check the form fields.');
  }
  return response;
}
async function json(path, options) {return (await api(path,options)).json();}
function run(handler) {return async event => {event?.preventDefault(); const button=event?.submitter||((event?.currentTarget?.tagName==='BUTTON')?event.currentTarget:null); if(button)button.disabled=true; try{notice('Working…'); await handler(event); if($('notice').textContent==='Working…')notice('Done.');}catch(e){notice(e.message,true);}finally{if(button)button.disabled=false;}};}
function signedOut() {token='';profile=null;stopRecording();window.speechSynthesis?.cancel();$('auth').hidden=false;$('workspace').hidden=true;$('logout').hidden=true;$('identity').textContent='Not signed in';['messages','memory-list','image-list','lesson-list','code-list','code-answer','photo-answer','mfa-secret'].forEach(id=>$(id).replaceChildren());photoURLs.forEach(URL.revokeObjectURL);photoURLs=[];lastCodeAnswer='';lastCodeQuestion='';document.querySelectorAll('textarea').forEach(t=>t.value='');}
async function signedIn(data) {token=data.access_token;profile=await json('/auth/me');$('auth').hidden=true;$('workspace').hidden=false;$('logout').hidden=false;$('identity').textContent=profile.username+' · '+profile.clearance;$('clearance-badge').textContent=profile.clearance;$('password').value='';$('otp').value='';$('auto-collect').checked=profile.auto_collect;$('mfa-status').textContent=profile.mfa_enabled?'MFA is enabled.':'MFA is not enabled yet.';const messages=await json('/conversations');$('messages').replaceChildren();messages.forEach(m=>bubble(m.speaker,m.message));notice('Welcome, '+profile.username+'.');}
function credentials(){return {username:$('username').value,password:$('password').value,otp:$('otp').value||null};}
$('auth-form').addEventListener('submit',run(async()=>signedIn(await json('/auth/login',{method:'POST',body:credentials()}))));
$('register').addEventListener('click',run(async()=>{if(!$('auth-form').reportValidity())return;await signedIn(await json('/auth/register',{method:'POST',body:credentials()}));}));
$('logout').addEventListener('click',run(async()=>{await api('/auth/logout',{method:'POST'});signedOut();notice('Signed out.');}));
function bubble(speaker,text){const el=document.createElement('div');el.className='bubble'+(speaker==='User'?' user':'');const label=document.createElement('small');label.textContent=speaker==='User'?'You':'Athena';el.append(label,document.createTextNode(text));$('messages').append(el);$('messages').scrollTop=$('messages').scrollHeight;}
function speak(text){if(!$('read-aloud').checked)return;const synth=window.speechSynthesis;if(!synth){notice('Speech output is not supported in this browser.',true);return;}const voice=synth.getVoices().find(v=>v.localService&&v.lang.startsWith('en'))||synth.getVoices().find(v=>v.localService);if(!voice){notice('No local speech voice found. Install a Windows speech voice.',true);return;}synth.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.voice=voice;synth.speak(utterance);}
$('chat-form').addEventListener('submit',run(async()=>{const message=$('message').value.trim();if(!message)return;const result=await json('/chat',{method:'POST',body:{message}});bubble('User',message);bubble('AI',result.response);$('message').value='';notice(result.memory_action?'Memory '+result.memory_action+'.':'Reply ready.');speak(result.response);}));
$('clear-chat').addEventListener('click',run(async()=>{if(!confirm('Clear your conversation history? Stored facts are kept separately.'))return;await api('/conversations',{method:'DELETE'});$('messages').replaceChildren();}));
function stopRecording(){if(recorder&&recorder.state==='recording')recorder.stop();if(recordingTimer)clearTimeout(recordingTimer);}
$('record').addEventListener('click',run(async()=>{
  if(recorder&&recorder.state==='recording'){stopRecording();return;}
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw new Error('Recording requires a supported browser on localhost or HTTPS.');
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});const chunks=[];
  const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(x=>MediaRecorder.isTypeSupported(x));
  recorder=new MediaRecorder(stream,mime?{mimeType:mime}:{});const currentToken=token;
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  recorder.onstop=async()=>{stream.getTracks().forEach(t=>t.stop());$('record').textContent='Record voice';try{if(!token||token!==currentToken)return;notice('Transcribing on your PC…');const body=new FormData();body.append('file',new Blob(chunks,{type:recorder.mimeType}),'voice.webm');const result=await json('/voice/transcribe',{method:'POST',body});if(token!==currentToken)return;$('message').value=result.text;notice(result.text?'Review your transcript, then send.':'No speech detected.');}catch(e){notice(e.message,true);}};
  recorder.start();$('record').textContent='Stop recording';recordingTimer=setTimeout(stopRecording,89000);notice('Recording…');
}));
function card(title,text){const el=document.createElement('article');el.className='card';const h=document.createElement('h3');h.textContent=title;const p=document.createElement('p');p.textContent=text;el.append(h,p);return el;}
function action(label,fn){const b=document.createElement('button');b.className='secondary';b.textContent=label;b.addEventListener('click',run(fn));return b;}
async function loadMemories(){const rows=await json('/memories');$('memory-list').replaceChildren();if(!rows.length)$('memory-list').textContent='No active memories yet. Try “I enjoy Python.”';rows.forEach(r=>{const el=card(r.relation.replaceAll('_',' '),r.value);el.append(action('Forget',async()=>{await api('/memories/'+r.id,{method:'DELETE'});await loadMemories();}));$('memory-list').append(el);});}
$('refresh-memories').addEventListener('click',run(loadMemories));
async function loadPhotos(){photoURLs.forEach(URL.revokeObjectURL);photoURLs=[];const rows=await json('/images');$('image-list').replaceChildren();for(const r of rows){const el=card('Picture '+r.id,r.caption);const img=document.createElement('img');img.alt=r.caption;const blob=await(await api('/images/'+r.id+'/content')).blob();const url=URL.createObjectURL(blob);photoURLs.push(url);img.src=url;el.prepend(img);el.append(action('Delete picture',async()=>{if(!confirm('Delete this stored picture and caption?'))return;await api('/images/'+r.id,{method:'DELETE'});await loadPhotos();}));$('image-list').append(el);}}
$('image-form').addEventListener('submit',run(async()=>{const file=$('image-file').files[0];if(file.size>8*1024*1024)throw new Error('Pictures must be under 8 MB.');const body=new FormData();body.append('file',file);body.append('caption',$('image-caption').value);body.append('describe',$('describe-image').checked);await api('/images',{method:'POST',body});$('image-form').reset();await loadPhotos();}));
$('photo-question').addEventListener('submit',run(async()=>{$('photo-answer').textContent=(await json('/images/ask',{method:'POST',body:{message:$('photo-query').value}})).response;}));
async function loadCode(){const rows=await json('/code');$('code-document').replaceChildren(new Option('No saved reference',''));$('code-list').replaceChildren();for(const r of rows){$('code-document').append(new Option(r.name,r.id));const el=card(r.name,r.content.slice(0,140));el.append(action('Open',async()=>{$('code-name').value=r.name;$('code-content').value=r.content;$('code-document').value=r.id;}),action('Delete',async()=>{await api('/code/'+r.id,{method:'DELETE'});await loadCode();}));$('code-list').append(el);}}
$('code-file').addEventListener('change',run(async()=>{const file=$('code-file').files[0];if(!file)return;if(file.size>50000)throw new Error('Load a source file under 50 KB.');$('code-name').value=file.name;$('code-content').value=await file.text();}));
$('code-form').addEventListener('submit',run(async()=>{const result=await json('/code',{method:'POST',body:{name:$('code-name').value,content:$('code-content').value}});await loadCode();$('code-document').value=result.id;}));
$('code-question').addEventListener('submit',run(async()=>{lastCodeQuestion=$('code-query').value;const result=await json('/code/ask',{method:'POST',body:{message:lastCodeQuestion,level:$('code-level').value,document_id:Number($('code-document').value)||null}});lastCodeAnswer=result.response;$('code-answer').textContent=result.response;$('save-lesson').hidden=false;}));
$('save-lesson').addEventListener('click',run(async()=>{await switchTab('learning');$('lesson-prompt').value=lastCodeQuestion;$('lesson-answer').value=lastCodeAnswer;$('lesson-level').value=$('code-level').value;$('lesson-approved').checked=false;notice('Check and correct the answer before approving it.');}));
async function loadLessons(){const rows=await json('/learning/examples');$('lesson-list').replaceChildren();rows.forEach(r=>{const el=card((r.approved?'Approved · ':'Review needed · ')+r.level,r.prompt);const answer=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Read answer';const p=document.createElement('p');p.className='answer';p.textContent=r.answer;answer.append(summary,p);el.append(answer,action(r.approved?'Unapprove':'Approve',async()=>{await api('/learning/examples/'+r.id,{method:'PATCH',body:{approved:!r.approved}});await loadLessons();}),action('Delete',async()=>{await api('/learning/examples/'+r.id,{method:'DELETE'});await loadLessons();}));$('lesson-list').append(el);});}
$('lesson-form').addEventListener('submit',run(async()=>{await api('/learning/examples',{method:'POST',body:{prompt:$('lesson-prompt').value,answer:$('lesson-answer').value,level:$('lesson-level').value,approved:$('lesson-approved').checked}});$('lesson-form').reset();await loadLessons();}));
$('auto-collect').addEventListener('change',run(async()=>{await api('/learning/collection',{method:'PUT',body:{enabled:$('auto-collect').checked}});}));
$('import-history').addEventListener('click',run(async()=>{const result=await json('/learning/import-history',{method:'POST'});await loadLessons();notice(result.imported+' previous answers added for review.');}));
$('export-lessons').addEventListener('click',run(async()=>{const blob=await(await api('/learning/export')).blob();if(!blob.size)throw new Error('Approve some examples first.');const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='athena-user-'+profile.id+'.jsonl';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}));
$('mfa-setup').addEventListener('click',run(async()=>{const data=await json('/auth/mfa/setup',{method:'POST',body:{password:$('mfa-password').value}});$('mfa-secret').textContent='Enter this setup key into your authenticator app: '+data.secret;}));
$('mfa-form').addEventListener('submit',run(async()=>{const data=await json('/auth/mfa/confirm',{method:'POST',body:{password:$('mfa-password').value,otp:$('mfa-code').value}});token=data.access_token;$('mfa-secret').textContent='';$('mfa-form').reset();$('mfa-status').textContent='MFA is enabled.';}));
async function switchTab(name){if(!token){notice('Sign in first.');return;}document.querySelectorAll('.tab').forEach(t=>t.hidden=t.id!=='tab-'+name);document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));if(name==='memories')await loadMemories();if(name==='photos')await loadPhotos();if(name==='code')await loadCode();if(name==='learning')await loadLessons();}
document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',run(()=>switchTab(b.dataset.tab))));

function updateConnection(){const online=navigator.onLine;$('connection').textContent=online?'Online':'Offline';$('connection').classList.toggle('offline',!online);if(!online)notice('Athena is offline. Reconnect to use your private workspace.',true);}
window.addEventListener('online',updateConnection);
window.addEventListener('offline',updateConnection);
updateConnection();
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;$('install-app').hidden=false;});
$('install-app').addEventListener('click',async()=>{if(!installPrompt)return;installPrompt.prompt();await installPrompt.userChoice;installPrompt=null;$('install-app').hidden=true;});
window.addEventListener('appinstalled',()=>{installPrompt=null;$('install-app').hidden=true;notice('Athena is installed.');});
if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>notice('App installation is unavailable in this browser.',true)));}
