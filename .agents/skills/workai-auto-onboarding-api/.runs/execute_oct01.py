from resume_oct01 import *
assert s['preflight_completed']
def detail(i):return req('GET',f"/issues/{i['issue_id']}")['data']
def sync(i):
 blocks=[]
 for wk in list(cache):
  w=week(wk,True)
  for day,allocs in w['data']['allocations'].items():
   for a in allocs:
    if a['issue_id']==i['issue_id']:
     blocks.append({'date':day,'hours':float(a['planned_hours']),'allocation_id':a['id'],'verified_at':datetime.now().isoformat()})
 i['blocks']=blocks;save();return sum(b['hours'] for b in blocks)
for i in s['items']:
 try:
  for b in i['planned_blocks']:week(b['date'])
  if not i.get('issue_id'):
   fields=['client_request_id','project_id','project_name','issue_type','summary','estimated_hours','optional_context']
   payload={k:i[k] for k in fields};payload.update(description='',acceptance_criteria=[])
   result=req('POST','/issues',payload)['data'];i['issue_id']=result['id'];i['issue_key']=result.get('issue_key') or result.get('jira_issue_key');i['status']='issue_created';i['last_verified_step']='issue_created';save()
  x=detail(i);i['issue_key']=x.get('issue_key') or x.get('jira_issue_key') or i['issue_key'];save()
  if x.get('assignee_id') not in (None,168):raise RuntimeError('ASSIGNEE_CONFLICT')
  if x.get('assignee_id') is None:req('PUT',f"/issues/{i['issue_id']}",{'assignee_id':168});i['last_verified_step']='assigned';save()
  if x['status']!='In Progress':
   req('POST',f"/issues/{i['issue_id']}/transition",{'client_request_id':i['client_request_id']+'-transition-in-progress','project_id':i['project_id'],'issue_key':i['issue_key'],'transition_id':'wf_to_do_in_progress','date':i['start_date'],'hours':i['estimated_hours']});i['last_verified_step']='transitioned';save()
  done=sync(i);d=date.fromisoformat(i['start_date'])
  for n in range(90):
   if done>=i['estimated_hours']-0.00001:break
   day=str(d);w=week(day,True)
   existing=[a for a in w['data']['allocations'].get(day,[]) if a['issue_id']==i['issue_id']]
   if not existing:
    h=round(min(i['estimated_hours']-done,capacity(w,day)),2)
    if h>0:
     cid=i['client_request_id']+'-'+day+'-'+str(h)+'h'
     i['pending_allocation']={'date':day,'hours':h,'client_request_id':cid};save()
     req('POST','/time-allocations',{'client_request_id':cid,'issue_id':i['issue_id'],'allocation_date':day,'planned_hours':h});i['last_verified_step']='allocation_written';save()
   done=sync(i);i['status']='partially_scheduled';save();d+=timedelta(days=1)
  if abs(done-i['estimated_hours'])>0.00001:raise RuntimeError('ALLOCATION_TOTAL_MISMATCH')
  x=detail(i)
  if not i.get('content_applied'):
   overview=(ROOT/('project_overview_mob_era_85.md' if i['project_id']==85 else 'Project_Overview_WarSurvival_115.md')).read_text(encoding='utf-8-sig')
   payload={k:i[k] for k in ['project_id','project_key','project_name','issue_type','summary','estimated_hours','optional_context']};payload['project_overview']=overview
   fallback=None
   try:
    gen=req('POST','/issues/quick-create/suggest-description',payload,30)['data'];desc=gen.get('suggested_description');criteria=gen.get('suggested_acceptance_criteria')
    if not desc or not criteria:fallback='Missing suggested content'
   except Exception as e:
    if 'CURL_ERROR_28' in str(e) or 'AI_GENERATION_FAILED' in str(e):fallback=str(e)
    else:raise
   if fallback:
    i['fallback_used']=True;i['fallback_reason']=fallback
    desc=i['summary']+'. '+('Chuẩn bị bản build đúng phiên bản và kiểm tra khả năng cài đặt, khởi động, chơi game trên nền tảng đích.' if i['row_number']<=2 else 'Thực hiện và kiểm tra trong gameplay của dự án, ghi nhận kết quả kiểm thử.')
    texts={1:['Tạo được bản build iOS phiên bản 0,3,2.','Cài đặt và khởi động được bản build trên thiết bị iOS kiểm thử.','Chạy được một lượt chơi và ghi nhận kết quả kiểm tra.'],2:['Tạo được bản build Android phiên bản 0,0,3,9.','Cài đặt và khởi động được bản build trên thiết bị Android kiểm thử.','Chạy được một lượt chơi và ghi nhận kết quả kiểm tra.'],3:['Các lỗi era rush đã xử lý có bước tái hiện và kết quả kiểm thử lại.','Có số liệu đo trước và sau cho phần tối ưu đã thực hiện.','Tài liệu mô tả luồng chơi era rush và các thay đổi đã thực hiện.'],4:['Boss undying được cấu hình và xuất hiện trong màn kiểm thử CrowdBattle.','Kiểm tra và ghi nhận hoạt động tấn công, nhận sát thương và kết thúc trận theo cấu hình boss.','Chơi lại màn không còn trạng thái boss của lượt trước.']}[i['row_number']]
    criteria=[{'text':t,'weight':1,'evidence_types':['link'],'evidence_hint':'Link bản build, tài liệu hoặc kết quả kiểm thử'} for t in texts]
   req('PUT',f"/issues/{i['issue_id']}",{'description':desc,'acceptance_criteria':criteria});i['last_verified_step']='content_saved';save()
  x=detail(i);total=sync(i)
  i['content_applied']=bool(x.get('description') and x.get('acceptance_criteria_items'))
  if x.get('assignee_id')!=168 or not i['content_applied'] or abs(total-i['estimated_hours'])>0.00001:raise RuntimeError('FINAL_VERIFICATION_FAILED')
  i['status']='completed';i['error']=None;i['last_verified_step']='completed';i.pop('pending_allocation',None);save()
  print(json.dumps({'row':i['row_number'],'id':i['issue_id'],'key':i['issue_key'],'status':i['status'],'blocks':i['blocks'],'fallback':i['fallback_used']},ensure_ascii=False),flush=True)
 except Exception as e:
  i['error']=str(e);i['status']='partially_scheduled' if i['blocks'] else 'failed';save();print(json.dumps({'row':i['row_number'],'error':str(e)}),flush=True)
  if any(z in str(e) for z in ['HTTP_403','UNAUTHENTICATED','FORBIDDEN']):break
