import sys, io
sys.path.insert(0, 'd:/prj/RSSHub-python')
import rsshub
app = rsshub.create_app('development')
c = app.test_client()
r = c.get('/feeds')
body = r.data.decode('utf-8')
io.open('d:/prj/RSSHub-python/_feeds.html', 'w', encoding='utf-8').write(body)
print('status:', r.status_code)
print('len:', len(body))
print('has Prudential card:', 'Prudential 香港保诚' in body)
print('has prudential route code:', 'prudential/knowledge-corner' in body)
