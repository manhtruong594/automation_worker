import json, os, subprocess, tempfile
from pathlib import Path
from datetime import date,timedelta,datetime
ROOT=Path.cwd(); STATE=ROOT/'.agents/skills/workai-auto-onboarding-api/.runs/workai-batch-ee8f2e42c442da38.json'
s=json.loads(STATE.read_text(encoding='utf-8-sig'))
def save():
 p=STATE.with_suffix('.tmp'); p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(p,STATE)
def req(method,path,payload=None,timeout=60):
 token=os.environ.get('WORKAI_TOKEN'); session=os.environ.get('WORKAI_SESSION_TOKEN'); value=token or session
 if not value: raise RuntimeError('MISSING_CREDENTIAL')
 if '\n' in value or '\r' in value: raise RuntimeError('INVALID_CREDENTIAL')
 value=value.replace('\\','\\\\').replace('"','\\"')
 cfg='header = "'+('Authorization: Bearer '+value if token else 'Cookie: sessionToken='+value)+'"\n'
 with tempfile.TemporaryDirectory() as td:
  out=Path(td)/'response'; cmd=['curl.exe','-q','--config','-','--silent','--show-error','--request',method,'--max-time',str(timeout),'--header','Accept: application/json','--output',str(out),'--write-out','%{http_code}\\n%header{cf-ray}']
  if payload is not None:
   p=Path(td)/'request.json'; p.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8'); cmd+=['--header','Content-Type: application/json','--data-binary','@'+str(p)]
  r=subprocess.run(cmd+['https://workai-be.horusjsc.com/api'+path],input=cfg,text=True,encoding='utf-8',capture_output=True)
  status,_,ray=r.stdout.partition('\n'); body=out.read_text(encoding='utf-8') if out.exists() else ''
  if r.returncode: raise RuntimeError('CURL_ERROR_'+str(r.returncode))
  if not status.startswith('2'): 
   try: err=json.loads(body).get('error',{})
   except: err={'code':'HTTP_'+status,'ray_id':ray.strip()}
   raise RuntimeError(json.dumps(err))
  data=json.loads(body)
  if not data.get('success'): raise RuntimeError(str(data.get('error')))
  return data
cache={}
def week(day,fresh=False):
 d=date.fromisoformat(day); a=d-timedelta(days=d.weekday()); key=str(a)
 if fresh or key not in cache: cache[key]=req('GET',f'/time-allocations?start_date={a}&end_date={a+timedelta(days=6)}')
 return cache[key]
def capacity(w,day):
 if w['meta']['user_id']!=168: raise RuntimeError('ASSIGNEE_NOT_CURRENT_USER')
 if not w['meta'].get('can_edit') or w['meta'].get('locked_periods'): return 0
 ds=next((x for x in w['data']['daily_summary'] if x['date']==day),{})
 cap=ds.get('actual_work_hours',0) or ds.get('standard_hours',0)
 if ds.get('status')=='weekend' or ds.get('is_day_off') or cap<=0:return 0
 idle=ds.get('idle_hours')
 return max(0,float(idle if isinstance(idle,(int,float)) else cap-ds.get('total_allocated_hours',0)))
if __name__=='__main__':
 try:
  reservations={}
  for i in s['items']:
   left=i['estimated_hours']; d=date.fromisoformat(i['start_date']); plan=[]
   for n in range(90):
    day=str(d); w=week(day); free=max(0,capacity(w,day)-reservations.get(day,0)); h=min(left,free)
    if h: plan.append({'date':day,'hours':h}); reservations[day]=reservations.get(day,0)+h; left-=h
    if left<=0:break
    d+=timedelta(days=1)
   if left:raise RuntimeError('NO_CAPACITY_WITHIN_90_DAYS')
   i['planned_blocks']=plan; i['error']=None; i['status']='pending'; i['last_verified_step']='preflight'
  s['preflight_completed']=True; save(); print(json.dumps({'plans':[{'row':i['row_number'],'plan':i['planned_blocks']} for i in s['items']]},ensure_ascii=False))
 except Exception as e:
  s['preflight_completed']=False
  for i in s['items']:i['error']=str(e);i['status']='failed'
  save(); print(str(e)); raise SystemExit(1)
