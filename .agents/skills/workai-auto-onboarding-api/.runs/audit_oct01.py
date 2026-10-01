from resume_oct01 import *
for i in s['items']:
 x=req('GET',f"/issues/{i['issue_id']}")['data']
 assert x['status']=='In Progress' and x['assignee_id']==168
 assert x.get('description') and x.get('acceptance_criteria_items')
 i['verified_server_status']=x['status']
 for b in i['blocks']:
  h=b['hours']; hv=str(int(h)) if h==int(h) else str(h)
  b['client_request_id']=i['client_request_id']+'-'+b['date']+'-'+hv+'h'
 for b in i.get('planned_blocks',[]):b['hours']=round(b['hours'],2)
s.pop('server_mutations',None)
s['verified_completed_count']=sum(i['status']=='completed' for i in s['items']);save()
print(json.dumps({'completed':s['verified_completed_count'],'fallback_count':sum(i['fallback_used'] for i in s['items'])}))
