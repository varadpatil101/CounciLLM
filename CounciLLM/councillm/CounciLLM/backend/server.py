"""Local-only CounciLLM server: static UI, persistent chats, and GGUF routing."""
from __future__ import annotations
import argparse, base64, json, os, re, shutil, socket, subprocess, threading, time, uuid, zipfile, zlib
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from xml.etree import ElementTree
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent.parent; CONFIG=ROOT/'config'/'council.json'; STATE=ROOT/'work'/'state.json'; MAX_FILE=12*1024*1024
def stamp(): return datetime.now(timezone.utc).isoformat()
def packed(x): return json.dumps(x,ensure_ascii=False,indent=2).encode()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def resolve(value, config):
 p=Path(os.path.expandvars(value)); return p if p.is_absolute() else (config.parent/p).resolve()
def call(url,method='GET',body=None,timeout=300):
 data=packed(body) if body is not None else None; headers={'Accept':'application/json'}
 if data: headers['Content-Type']='application/json'
 with urlopen(Request(url,data=data,headers=headers,method=method),timeout=timeout) as r: raw=r.read().decode()
 return json.loads(raw) if raw else {}
def port():
 with socket.socket() as s: s.bind(('127.0.0.1',0)); return s.getsockname()[1]
def llama():
 override=os.environ.get('COUNCILLM_LLAMA_SERVER')
 if override and Path(override).is_file(): return Path(override)
 root=Path.home()/'.lmstudio'/'extensions'/'backends'
 # CPU is the reliable default: it avoids competing for GPU memory with other
 # local model processes.  Set COUNCILLM_LLAMA_SERVER to opt into CUDA/Vulkan.
 found=[] if not root.is_dir() else list(root.glob('llama.cpp-win-x86_64-avx2-*/llama-server.exe'))
 return sorted(found,key=lambda x:x.parent.name)[-1] if found else None
def obj(text):
 try: return json.loads(text)
 except json.JSONDecodeError:
  m=re.search(r'\{.*\}',text,re.S)
  try: return json.loads(m.group()) if m else {}
  except json.JSONDecodeError: return {}
def clean_reply(text):
 """Hide chat-template tokens emitted by some GGUF chat templates."""
 text=re.sub(r'<\|(?:im_end|endoftext|assistant|eot_id)\|>','',text or '')
 return text.strip()
def artifact_name(value, extension):
 base=re.sub(r'[^A-Za-z0-9._ -]+','-',str(value or 'council-artifact')).strip(' .-') or 'council-artifact'
 return base[:80] + extension
def xml_escape(text):
 return (text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;'))
def document_bytes(kind, content):
 lines=[line for line in str(content).splitlines() if line.strip()] or ['']
 if kind=='pdf':
  stream='BT /F1 11 Tf 50 780 Td 14 TL ' + ' '.join(f'({line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")}) Tj T*' for line in lines[:55]) + ' ET'
  parts=['%PDF-1.4\n','1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n','2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n','3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n','4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n',f'5 0 obj<< /Length {len(stream.encode("latin-1", "replace"))} >>stream\n{stream}\nendstream\nendobj\n']
  offsets=[]; data=''
  for part in parts: offsets.append(len(data.encode('latin-1','replace')));data+=part
  start=len(data.encode('latin-1','replace'));data+='xref\n0 6\n0000000000 65535 f \n'+''.join(f'{offset:010d} 00000 n \n' for offset in offsets)+'trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(start)+'\n%%EOF\n'
  return data.encode('latin-1','replace')
 if kind=='docx':
  body=''.join(f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r></w:p>' for line in lines)
  output=__import__('io').BytesIO()
  with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
   z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
   z.writestr('word/document.xml',f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}<w:sectPr/></w:body></w:document>')
  return output.getvalue()
 if kind=='pptx':
  text=' '.join(lines)
  output=__import__('io').BytesIO()
  with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
   z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
   z.writestr('ppt/presentation.xml','<?xml version="1.0"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst><p:sldSz cx="9144000" cy="5143500"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
   z.writestr('ppt/_rels/presentation.xml.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>')
   z.writestr('ppt/slides/slide1.xml',f'<?xml version="1.0"?><p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/><p:sp><p:nvSpPr/><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{xml_escape(text)}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>')
  return output.getvalue()
 return str(content).encode('utf-8')

class Store:
 def __init__(self):
  self.lock=threading.RLock(); self.data=self.read()
 def default(self): return {'settings':{'name':'Local Admin','instructions':'You are an expert, air-gapped sovereign AI assistant. Do not assume internet connectivity.','font':'serif','theme':'dark','language':'English'},'projects':[{'id':'workspace','name':'CounciLLM Workspace','path':str(ROOT),'created_at':stamp()}],'active_project_id':'workspace','sessions':[]}
 def read(self):
  try:
   data={**self.default(),**load(STATE)} if STATE.is_file() else self.default()
   for session in data['sessions']: session.setdefault('pinned',False);session.setdefault('archived',False);session.setdefault('messages',[])
   return data
  except Exception: return self.default()
 def save(self):
  STATE.parent.mkdir(parents=True,exist_ok=True); temp=STATE.with_suffix('.tmp'); temp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(STATE)
 def session(self,id): return next((x for x in self.data['sessions'] if x['id']==id),None)
 def create(self,title='New chat'):
  x={'id':str(uuid.uuid4()),'title':title[:80],'created_at':stamp(),'updated_at':stamp(),'pinned':False,'archived':False,'messages':[]}; self.data['sessions'].insert(0,x); self.save(); return x
 def active(self): return next((x for x in self.data['projects'] if x['id']==self.data['active_project_id']),self.data['projects'][0])
 def append(self,sid,user,reply,meta,attachments=None):
  with self.lock:
   s=self.session(sid) if sid else None
   if not s: s=self.create(user[:64] or 'New chat')
   user_message={'id':str(uuid.uuid4()),'role':'user','content':user,'created_at':stamp()}
   if attachments:user_message['attachments']=attachments
   s['messages'] += [user_message,{'id':str(uuid.uuid4()),'role':'assistant','content':reply,'metadata':meta,'created_at':stamp()}]
   s['updated_at']=stamp(); s['title']=user[:64] if len(s['messages'])==2 else s['title']; self.data['sessions'].sort(key=lambda x:(not x['pinned'],x['updated_at'])); self.save(); return s
 def clear_account_data(self):
  """Remove only CouncilLM-owned user content, never the program or model config."""
  with self.lock:
   for target in (STATE, ROOT/'attachments', ROOT/'artifacts', ROOT/'work'/'projects'):
    if target.is_dir(): shutil.rmtree(target)
    elif target.is_file(): target.unlink()
   self.data=self.default()

class Run:
 def __init__(self,model,runtime): self.model,self.runtime,self.port,self.proc=model,runtime,port(),None; self.lock=threading.RLock()
 @property
 def url(self): return f'http://127.0.0.1:{self.port}'
 def live(self): return bool(self.proc and self.proc.poll() is None)
 def ready(self):
  try: return bool(call(self.url+'/v1/models',timeout=2))
  except Exception:return False
 def start(self):
  with self.lock:
   if self.live() and self.ready(): return
   # A process that survived but never reached its HTTP-ready state must not
   # be left resident before another server is started for the same model.
   if self.live(): self.stop()
   if not self.model['path'].is_file() or (self.model.get('mmproj') and not self.model['mmproj'].is_file()): raise RuntimeError(f"Missing local model file for {self.model['display_name']}.")
   if not self.runtime: raise RuntimeError('No local llama-server executable was found.')
   args=[str(self.runtime),'--host','127.0.0.1','--port',str(self.port),'--model',str(self.model['path']),'--alias',self.model['alias'],'--ctx-size',str(self.model['ctx']),'--log-disable','--jinja']
   if self.model.get('mmproj'): args += ['--mmproj',str(self.model['mmproj'])]
   (ROOT/'logs').mkdir(exist_ok=True); log=(ROOT/'logs'/f"{self.model['id']}-{self.port}.log").open('a',encoding='utf-8')
   try:self.proc=subprocess.Popen(args,cwd=str(self.runtime.parent),stdout=log,stderr=subprocess.STDOUT,text=True)
   finally:log.close()
   deadline=time.monotonic()+180
   while time.monotonic()<deadline:
    if self.proc.poll() is not None: raise RuntimeError(f"{self.model['display_name']} stopped while loading; see logs.")
    if self.ready(): return
    time.sleep(.4)
   raise RuntimeError(f"Timed out loading {self.model['display_name']}.")
 def chat(self,messages,temp=None,max_tokens=None):
  self.start(); return call(self.url+'/v1/chat/completions','POST',{'model':self.model['alias'],'messages':messages,'temperature':self.model['temperature'] if temp is None else temp,'max_tokens':self.model['tokens'] if max_tokens is None else max_tokens,'stream':False})
 def stop(self):
  with self.lock:
   if self.live():
    self.proc.terminate()
    try:self.proc.wait(8)
    except subprocess.TimeoutExpired:self.proc.kill()
   self.proc=None

class Council:
 def __init__(self,config,store):
  raw=load(config); self.store=store; self.runtime=llama(); self.runs={}; self.request_lock=threading.Lock(); self.active_specialist=None
  self.models={}
  for x in raw['models']:
   self.models[x['role']]={'id':x['id'],'role':x['role'],'display_name':x.get('display_name',x['id']),'alias':x.get('alias',x['id']),'path':resolve(x['path'],config),'mmproj':resolve(x['mmproj'],config) if x.get('mmproj') else None,'ctx':int(x.get('ctx_size',8192)),'tokens':int(x.get('max_tokens',1024)),'temperature':float(x.get('temperature',.2)),'notes':x.get('notes','')}
 def get(self,role):
  if role not in self.runs:self.runs[role]=Run(self.models[role],self.runtime)
  return self.runs[role]
 def status(self): return [{**{k:v for k,v in x.items() if k not in {'path','mmproj'}},'available':x['path'].is_file() and (not x['mmproj'] or x['mmproj'].is_file()),'running':self.runs[x['role']].live() if x['role'] in self.runs else False} for x in self.models.values()]
 def heuristic(self,text,files):
  t=text.lower()
  if any(x['kind']=='image' for x in files) or any(x in t for x in ('image','photo','screenshot','diagram','ocr','visual')): return 'vision','Visual input or a visual request was detected.'
  if any(x in t for x in ('code','bug','traceback','python','javascript','typescript','html','css','refactor','debug','api','compile','backend','frontend','git')): return 'coding','Implementation or code language was detected.'
  return 'general','No specialist signal was needed.'
 def route(self,text,files):
  fallback,reason=self.heuristic(text,files); router=self.get('router')
  try:
   r=router.chat([{'role':'system','content':"You are a deterministic local router. Select ONLY general, coding, or vision."},{'role':'user','content':f'Return only JSON {{"route":"general|coding|vision","reason":"brief","confidence":0.0}}. User request: {text} /no_think'}],0,128)
   raw=r['choices'][0]['message'].get('content',''); parsed=obj(raw); role=str(parsed.get('route','')).lower().strip()
   if any(file['kind']=='image' for file in files):
    return {'role':'vision','reason':'A local image attachment requires the vision specialist.','confidence':1.0,'source':'attachment'}
   return {'role':role if role in {'general','coding','vision'} else fallback,'reason':str(parsed.get('reason') or reason),'confidence':parsed.get('confidence',.7),'source':'router'}
  except Exception as e:return {'role':fallback,'reason':reason+' Router fallback: '+str(e),'confidence':.5,'source':'heuristic'}
  finally: router.stop()
 def chat(self,data):
  # llama.cpp model lifecycle is intentionally sequential: router -> specialist.
  # Serializing requests prevents two browser sends from competing for the same
  # RAM/VRAM while one model is unloading and another is starting.
  with self.request_lock:
   return self._chat(data)
 def _chat(self,data):
  text=str(data.get('message','')).strip()
  if not text:raise ValueError('Write a message before sending.')
  files=attachments(data.get('attachments',[])); saved_files=persist_attachments(files,Path(self.store.active()['path'])); requested=str(data.get('model','auto')).lower()
  has_image=any(file['kind']=='image' for file in files)
  route=({'role':'vision','reason':'A local image attachment was detected and handed to the vision specialist.','confidence':1.0,'source':'attachment'} if requested=='auto' and has_image else self.route(text,files) if requested=='auto' else {'role':requested,'reason':'Manually selected by user.','confidence':1,'source':'manual'})
  if route['role'] not in {'general','coding','vision'}:raise ValueError('Select Auto Router, General, Coding, or Vision.')
  content=text
  image=[x for x in files if x['kind']=='image']
  if image and route['role']=='vision': content=[{'type':'text','text':text}]+[{'type':'image_url','image_url':{'url':x['data_url']}} for x in image]
  else:
   texts=[x['text'] for x in files if x['kind']=='text']
   if texts:content+='\n\nAttached local file content:\n'+'\n\n'.join(texts)
  hist=[{'role':x['role'],'content':x['content']} for x in data.get('history',[])[-16:] if x.get('role') in {'user','assistant'} and isinstance(x.get('content'),str)]
  instruction=self.store.data['settings']['instructions']+'\nYou are fully offline: never claim web or cloud access.'
  # Router is released after its decision. Keep exactly one specialist loaded
  # as well, so switching general/coding/vision cannot accumulate model RAM.
  for role, process in self.runs.items():
   if role not in {'router', route['role']}: process.stop()
  run=self.get(route['role']); result=run.chat([{'role':'system','content':instruction}]+hist+[{'role':'user','content':content}]); self.active_specialist=route['role']
  choice=result['choices'][0]['message']; reply=clean_reply(choice.get('content') or choice.get('reasoning_content') or '')
  if not reply:raise RuntimeError('The local model returned no visible response.')
  trace=([{'step':'Start local router','status':'done','detail':'Router evaluated the prompt first.'},{'step':'Hand off to specialist','status':'done','detail':run.model['display_name']}] if requested=='auto' else [{'step':'Use selected model','status':'done','detail':run.model['display_name']}]) + [{'step':'Generate offline response','status':'done','detail':'Completed through local llama.cpp.'}]
  session=self.store.append(data.get('session_id'),text,reply,{'route':route,'model':run.model['id'],'trace':trace},saved_files)
  return {'status':'ok','reply':reply,'route':route,'model':{'id':run.model['id'],'role':run.model['role'],'display_name':run.model['display_name']},'trace':trace,'usage':result.get('usage'),'session':session}
 def shutdown(self):
  for x in self.runs.values():x.stop()

def office_text(raw, extension):
 """Extract visible text from modern Office XML containers without a cloud API."""
 try:
  with zipfile.ZipFile(__import__('io').BytesIO(raw)) as archive:
   if extension=='.docx': names=['word/document.xml']
   elif extension=='.pptx': names=sorted(n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n))
   else: names=['xl/sharedStrings.xml']+[n for n in archive.namelist() if n.startswith('xl/worksheets/') and n.endswith('.xml')]
   chunks=[]
   for name in names:
    if name not in archive.namelist(): continue
    root=ElementTree.fromstring(archive.read(name))
    text=' '.join(part.strip() for part in root.itertext() if part.strip())
    if text: chunks.append(text)
   return '\n\n'.join(chunks)[:100000]
 except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as exc: raise ValueError(f'Could not read this {extension[1:].upper()} file locally.') from exc
def pdf_text(raw):
 """Best-effort local extraction for ordinary Flate-compressed PDF text streams."""
 chunks=[]
 for stream in re.findall(rb'stream\r?\n(.*?)\r?\nendstream',raw,re.S):
  try: stream=zlib.decompress(stream)
  except zlib.error: pass
  for block in re.findall(rb'\((?:\\.|[^\\)])*\)\s*(?:Tj|\')|\[(.*?)\]\s*TJ',stream,re.S):
   value=block if isinstance(block,bytes) else b''
   if not value: continue
   for part in re.findall(rb'\((?:\\.|[^\\)])*\)',value): chunks.append(re.sub(rb'\\([()\\])',rb'\1',part[1:-1]).decode('latin-1','replace'))
  for part in re.findall(rb'\((?:\\.|[^\\)])*\)\s*Tj',stream): chunks.append(re.sub(rb'\\([()\\])',rb'\1',part[:-2].strip()[1:-1]).decode('latin-1','replace'))
 result=' '.join(chunks).strip()
 if not result: raise ValueError('This PDF has no extractable text. Attach page images for scanned PDFs.')
 return result[:100000]
def attachments(items):
 result=[]
 for x in items[:4] if isinstance(items,list) else []:
  if not isinstance(x,dict):continue
  data=str(x.get('data_url','')); name=str(x.get('name','attachment')); typ=str(x.get('type',''))
  if not data.startswith('data:') or ',' not in data:continue
  try:raw=base64.b64decode(data.split(',',1)[1],validate=True)
  except Exception:raise ValueError(f'{name} is not a valid local file.')
  if len(raw)>MAX_FILE:raise ValueError(f'{name} is larger than 12 MB.')
  extension=Path(name).suffix.lower()
  if typ.startswith('image/'):result.append({'kind':'image','name':name,'type':typ,'data_url':data,'raw':raw})
  elif typ.startswith('text/') or extension in {'.py','.js','.ts','.html','.css','.md','.txt','.json','.csv','.xml','.rtf','.yaml','.yml','.sql'}:result.append({'kind':'text','name':name,'type':typ,'text':raw.decode('utf-8','replace')[:100000],'raw':raw})
  elif extension in {'.docx','.pptx','.xlsx'}:result.append({'kind':'text','name':name,'type':typ,'text':office_text(raw,extension),'raw':raw})
  elif extension=='.pdf':result.append({'kind':'text','name':name,'type':typ,'text':pdf_text(raw),'raw':raw})
  elif extension in {'.doc','.ppt','.xls'}:raise ValueError(f'{name}: legacy {extension.upper()} is not supported locally. Save it as {extension}x and attach that file.')
  else:raise ValueError(f'{name}: use an image, PDF, DOCX, PPTX, XLSX, XML, or text/code file.')
 return result
def persist_attachments(files, root):
 """Keep user-shared files in the active local project for the file sidebar."""
 folder=root/'attachments'; saved=[]
 for file in files:
  name=re.sub(r'[^A-Za-z0-9._ -]+','-',file['name']).strip(' .-') or 'attachment'
  folder.mkdir(parents=True,exist_ok=True); target=folder/f'{int(time.time()*1000)}-{name}'
  target.write_bytes(file['raw'])
  saved.append({'name':name,'path':str(target.relative_to(root)).replace('\\','/'),'kind':file['kind'],'type':file.get('type','')})
 return saved
def tree(root):
 out=[]; blocked={'.git','__pycache__','logs','node_modules'}
 try:
  for p in sorted(root.rglob('*')):
   rel=p.relative_to(root)
   if any(x in blocked for x in rel.parts):continue
   out.append({'path':str(rel).replace('\\','/'),'directory':p.is_dir(),'size':None if p.is_dir() else p.stat().st_size})
   if len(out)>=120:break
 except OSError:pass
 return out

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass
 def sendj(self,status,data):
  b=packed(data);self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n>20*1024*1024:raise ValueError('Request is too large.')
  x=json.loads(self.rfile.read(n).decode() if n else '{}')
  if not isinstance(x,dict):raise ValueError('Expected JSON object.')
  return x
 @property
 def council(self):return self.server.council
 @property
 def store(self):return self.server.store
 def do_GET(self):
  u=urlparse(self.path); p=u.path
  if p=='/api/health':self.sendj(200,{'status':'ok','mode':'offline','runtime_available':bool(self.council.runtime),'models':self.council.status()});return
  if p in {'/api/bootstrap','/api/state'}:
   d=self.store.data;self.sendj(200,{'settings':d['settings'],'projects':d['projects'],'active_project_id':d['active_project_id'],'sessions':[{k:v for k,v in x.items() if k!='messages'} for x in d['sessions']],'artifacts':[x for x in tree(Path(self.store.active()['path'])) if x['path'].startswith('artifacts/') and not x['directory']],'models':self.council.status(),'files':tree(Path(self.store.active()['path'])),'runtime_available':bool(self.council.runtime)});return
  if p=='/api/models':self.sendj(200,{'runtime':str(self.council.runtime) if self.council.runtime else None,'models':self.council.status()});return
  if p.startswith('/api/sessions/'):
   x=self.store.session(p.rsplit('/',1)[1]);self.sendj(200,{'session':x}) if x else self.sendj(404,{'error':'Chat not found.'});return
  if p=='/api/files':
   rel=unquote(parse_qs(u.query).get('path',[''])[0]);root=Path(self.store.active()['path']).resolve();f=(root/rel).resolve()
   if root not in f.parents or not f.is_file():self.sendj(404,{'error':'File not found.'});return
   if f.stat().st_size>512000:self.sendj(400,{'error':'File is too large to preview.'});return
   self.sendj(200,{'path':str(f.relative_to(root)),'content':f.read_text(encoding='utf-8',errors='replace')});return
  super().do_GET()
 def do_POST(self):
  try:
   p=urlparse(self.path).path;d=self.body()
   if p=='/api/chat':self.sendj(200,self.council.chat(d));return
   if p=='/api/sessions':self.sendj(201,{'session':self.store.create(str(d.get('title','New chat')))});return
   if p=='/api/settings':
    with self.store.lock:self.store.data['settings'].update({k:v for k,v in d.items() if k in {'name','instructions','font','theme','language'}});self.store.save()
    self.sendj(200,{'settings':self.store.data['settings']});return
   if p=='/api/projects':
    name=str(d.get('name','')).strip()
    if not name:raise ValueError('A project name is required.')
    folder=re.sub(r'[^A-Za-z0-9._ -]+','-',name).strip(' .-') or 'project';path=ROOT/'work'/'projects'/folder;path.mkdir(parents=True,exist_ok=True);x={'id':str(uuid.uuid4()),'name':name,'path':str(path),'created_at':stamp()}
    with self.store.lock:self.store.data['projects'].append(x);self.store.data['active_project_id']=x['id'];self.store.save()
    self.sendj(201,{'project':x});return
   if p=='/api/projects/active':
    id=str(d.get('id','')); 
    if not any(x['id']==id for x in self.store.data['projects']):raise ValueError('Project not found.')
    with self.store.lock:self.store.data['active_project_id']=id;self.store.save()
    self.sendj(200,{'project':self.store.active(),'files':tree(Path(self.store.active()['path']))});return
   if p=='/api/artifacts':
    kind=str(d.get('type','txt')).lower(); extensions={'txt':'.txt','md':'.md','xml':'.xml','pdf':'.pdf','docx':'.docx','pptx':'.pptx'}
    if kind not in extensions: raise ValueError('Choose TXT, Markdown, XML, PDF, DOCX, or PPTX.')
    content=str(d.get('content','')).strip()
    if not content: raise ValueError('Artifact content is required.')
    folder=Path(self.store.active()['path'])/'artifacts';folder.mkdir(parents=True,exist_ok=True)
    target=folder/artifact_name(d.get('name'),extensions[kind]);target.write_bytes(document_bytes(kind,content) if kind in {'pdf','docx','pptx'} else content.encode('utf-8'))
    self.sendj(201,{'artifact':{'path':str(target.relative_to(Path(self.store.active()['path']))).replace('\\','/'),'size':target.stat().st_size}});return
   self.sendj(404,{'error':'Unknown local endpoint.'})
  except ValueError as e:self.sendj(400,{'status':'error','message':str(e)})
  except Exception as e:self.sendj(500,{'status':'error','message':str(e)})
 def do_PATCH(self):
  try:
   x=self.store.session(urlparse(self.path).path.rsplit('/',1)[1]);d=self.body()
   if not x:self.sendj(404,{'error':'Chat not found.'});return
   with self.store.lock:
    if isinstance(d.get('title'),str) and d['title'].strip():x['title']=d['title'].strip()[:80]
    if isinstance(d.get('pinned'),bool):x['pinned']=d['pinned']
    if isinstance(d.get('archived'),bool):x['archived']=d['archived']
    x['updated_at']=stamp();self.store.save()
   self.sendj(200,{'session':x})
  except ValueError as e:self.sendj(400,{'message':str(e)})
 def do_DELETE(self):
  path=urlparse(self.path).path
  if path=='/api/account/data':
   self.store.clear_account_data();self.sendj(200,{'status':'deleted'});return
  id=path.rsplit('/',1)[1]
  with self.store.lock:
   old=len(self.store.data['sessions']);self.store.data['sessions']=[x for x in self.store.data['sessions'] if x['id']!=id];self.store.save()
  self.sendj(200,{'status':'deleted'}) if old!=len(self.store.data['sessions']) else self.sendj(404,{'error':'Chat not found.'})

def main():
 a=argparse.ArgumentParser();a.add_argument('--host',default='127.0.0.1');a.add_argument('--port',type=int,default=8765);a.add_argument('--config',type=Path,default=CONFIG);x=a.parse_args();config=x.config.resolve();raw=load(config);front=resolve(raw.get('frontend_dir','../frontend'),config)
 if not front.is_dir():raise SystemExit(f'Frontend directory is missing: {front}')
 store=Store();server=ThreadingHTTPServer((x.host,x.port),lambda *p,**k:Handler(*p,directory=str(front),**k));server.store=store;server.council=Council(config,store);print(f'CounciLLM local server: http://{x.host}:{x.port}')
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.council.shutdown();server.server_close()
if __name__=='__main__':main()
