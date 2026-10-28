"""Test update workflow without depending on lottery provider network access."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile

source=Path(__file__).resolve().parent.parent/'scripts'/'update_data.py'
spec=importlib.util.spec_from_file_location('lotto_update',source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def draw(i):
 date=dt.date(2002,12,7)+dt.timedelta(days=7*(i-1))
 ns=[i, i+1, i+2, i+3, i+4, i+5]
 return {'round':i,'date':date.isoformat(),'nums':ns,'bonus':i+6}

def apirow(d):
 obj={'ltEpsd':d['round'],'ltRflYmd':d['date'].replace('-',''),'bnsWnNo':d['bonus']}
 obj.update({f'tm{i}WnNo':v for i,v in enumerate(d['nums'],1)})
 return obj

with tempfile.TemporaryDirectory() as tmp:
 mod.DB=Path(tmp)/'draws.json'
 doc={'draws':[draw(i) for i in range(8,11)],'source':'sample-only'}
 mod.DB.write_text(json.dumps(doc))
 def fake(endpoint,params=None):
  if endpoint=='selectPstLt645Info.do':return [apirow(draw(12))]
  center=params['srchLtEpsd']
  return [apirow(draw(i)) for i in range(max(1,center-4),min(12,center+5)+1)]
 mod.get_list=fake
 mod.time.sleep=lambda *_:None
 mod.run()
 result=json.loads(mod.DB.read_text())
 assert len(result['draws'])==12
 assert result['draws'][0]['round']==1 and result['draws'][-1]['round']==12
 assert result['latestRound']==12
 old=mod.DB.read_bytes()
 def fail(*_args,**_kwargs):raise RuntimeError('provider unavailable')
 mod.get_list=fail
 try:mod.run()
 except RuntimeError:pass
 else:raise AssertionError('expected failed fetch')
 assert old==mod.DB.read_bytes(), 'source failure must preserve archived data'
 bad=draw(1);bad['nums']=[1,1,2,3,4,5]
 try:mod.validate(bad)
 except ValueError:pass
 else:raise AssertionError('duplicate numbers must fail')
 print('SERVER UPDATE TEST PASS')
