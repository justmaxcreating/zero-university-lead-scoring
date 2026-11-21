import sys, pandas as pd
df=pd.read_csv(sys.argv[1]); outdir=sys.argv[2]
df['conv']=df.converted_to_paid.astype(str).str.lower()=='true'
SCHOOL_CAP=15
# (signal, column/metric, list of (condition text, threshold, points, test))
share=lambda r: r.weekly_active_users/r.total_members if r.total_members>0 else 0
SIGNALS=[
 ('Team size','company_domain_seats',lambda r:r.company_domain_seats,[('>=',25,30),('>=',5,10)]),
 ('Integrations','integrations_connected',lambda r:r.integrations_connected,[('>=',4,20),('=',3,15),('=',2,5)]),
 ('Teamspaces','teamspaces',lambda r:r.teamspaces,[('>=',5,15),('=',4,8),('=',3,4)]),
 ('Weekly active users','weekly_active_users',lambda r:r.weekly_active_users,[('>=',40,15),('>=',20,10),('>=',6,3)]),
 ('Active share','weekly_active_users / total_members (only if weekly_active_users >= 20)',lambda r:share(r) if r.weekly_active_users>=20 else 0,[('>=',0.25,5)]),
 ('Buying intent','pricing_page_visits_30d',lambda r:r.pricing_page_visits_30d,[('>=',10,15),('>=',5,8),('>=',3,4)]),
]
assert sum(max(p for _,_,p in t) for *_,t in SIGNALS)==100
def hit(v,op,th): return v>=th if op=='>=' else v==th
rows=[]
for _,r in df.iterrows():
    d={}; total=0
    for name,col,f,tiers in SIGNALS:
        v=f(r); pts=next((p for op,th,p in tiers if hit(v,op,th)),0)
        d['pts_'+name.lower().replace(' ','_')]=pts; total+=pts
    d['signal_points_raw']=total
    if r.student_signups>0:
        d['override']=f'Student signups > 0 ({r.student_signups}) -> score 0'; score=0
    elif r.domain_type in ('k12_school','university') or r.industry in ('K-12 Education','Higher Education'):
        d['override']=f'School/university -> capped at {SCHOOL_CAP}'; score=min(total,SCHOOL_CAP)
    elif r.domain_type!='company':
        d['override']='Not a company domain -> score 0'; score=0
    else:
        d['override']=''; score=total
    d['lead_score']=score
    d['tier']='Hot' if score>=70 else 'Warm' if score>=45 else 'Nurture' if score>=20 else 'Low'
    rows.append(d)
df=pd.concat([df,pd.DataFrame(rows,index=df.index)],axis=1)
assert df.lead_score.between(0,100).all()
print(df.groupby('tier').conv.agg(['count','sum','mean']).round(3))
print(df.override.value_counts())
cv=df[df.conv].lead_score; nc=df[~df.conv].lead_score
print('AUC',round(sum((a>b)+0.5*(a==b) for a in cv for b in nc)/(len(cv)*len(nc)),3))
# rules table
rr=[]
for o in [('Override 1','student_signups','> 0','0','Score forced to 0'),
          ('Override 2','domain_type / industry','k12_school or university, or K-12 / Higher Education industry',str(SCHOOL_CAP),f'Score capped at {SCHOOL_CAP} (stays Low)'),
          ('Override 3','domain_type','not company (e.g. personal)','0','Score forced to 0')]:
    rr.append(dict(zip(['signal','column','condition','threshold','points'],o)))
for name,col,_,tiers in SIGNALS:
    for op,th,p in tiers: rr.append(dict(signal=name,column=col,condition=op,threshold=th,points=p))
    rr.append(dict(signal=name,column=col,condition='otherwise',threshold='',points=0))
for t,c in [('Hot','70-100'),('Warm','45-69'),('Nurture','20-44'),('Low','0-19')]:
    rr.append(dict(signal='Tier: '+t,column='lead_score',condition='between',threshold=c,points=''))
pd.DataFrame(rr).to_csv(f'{outdir}/lead_score_rules.csv',index=False)
calls=df[~df.conv].sort_values(['lead_score','pricing_page_visits_30d'],ascending=False).copy()
calls.insert(0,'call_rank',range(1,len(calls)+1))
pc=[c for c in df.columns if c.startswith('pts_')]
cols=['call_rank','lead_score','tier','override','account_id','workspace_name','company_domain','domain_type','industry','country','rep_owner']+pc+['signal_points_raw','company_domain_seats','student_signups','total_members','weekly_active_users','integrations_connected','teamspaces','pricing_page_visits_30d','last_active_date']
calls[cols].to_csv(f'{outdir}/lead_scores_call_list.csv',index=False)
print(calls.tier.value_counts())
sch=df[df.override.str.startswith('Student')]; print('students: raw max',sch.signal_points_raw.max(),'final max',sch.lead_score.max())
print(calls.head(3)[cols[:4]+pc].to_string(index=False))
