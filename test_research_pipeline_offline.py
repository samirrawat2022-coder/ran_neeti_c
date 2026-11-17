import ast, pathlib, re, time, xml.etree.ElementTree as ET
from unittest.mock import patch
import requests
src=(pathlib.Path(__file__).resolve().parents[1] / 'app.py').read_text()
tree=ast.parse(src)
names={'google_news_search','format_research_context','call_gemini','build_prompt'}
body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
ns={'requests':requests,'re':re,'ET':ET,'time':time,'gemini_model':lambda:'gemini-3.8-flash'}
exec(compile(ast.Module(body=body,type_ignores=[]),'<app-functions>','exec'),ns)

class Resp:
    status_code=200
    content=b'''<rss><channel><item><title>Team A beats Team B</title><link>https://publisher.test/story</link><description>Latest update and match report</description><pubDate>Tue, 17 Nov 2026 10:00:00 GMT</pubDate><source>Sports Desk</source></item></channel></rss>'''
    def raise_for_status(self): pass
    def json(self): return {'candidates':[{'content':{'parts':[{'text':'RAN-NEETI analysis'}]}}]}

with patch.object(requests,'get',return_value=Resp()):
    rows=ns['google_news_search']('team A vs team B')
assert len(rows)==1 and rows[0]['source']=='Sports Desk' and rows[0]['url']=='https://publisher.test/story'
ctx=ns['format_research_context'](rows)
assert '[1]' in ctx and 'Sports Desk' in ctx and 'https://publisher.test/story' in ctx
prompt=ns['build_prompt']('SPORT','A vs B','none','Detailed','none',ctx)
assert 'RETRIEVED PUBLIC RESEARCH RESULTS' in prompt and 'Do not copy publisher wording' in prompt
captured={}
def fake_post(url, **kwargs):
    captured.update(kwargs)
    return Resp()
with patch.object(requests,'post',side_effect=fake_post):
    answer,sources,model=ns['call_gemini']('test prompt','fake-key')
assert answer=='RAN-NEETI analysis' and model=='gemini-3.8-flash'
assert 'tools' not in captured['json']
print('PASS: RSS parsing, evidence formatting, prompt construction, Gemini text-only payload')
