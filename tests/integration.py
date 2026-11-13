"""Integration checks against a new database in an isolated PostgreSQL cluster.

No existing database or table is deleted. Set PGHOST/PGPORT/PGUSER first.
Run from the project root: python tests/integration.py
"""
from pathlib import Path
import json
import os
import sys
import uuid
from datetime import date, timedelta

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if (ROOT/'.vendor_python').exists(): sys.path.insert(0,str(ROOT/'.vendor_python'))
import psycopg2
from psycopg2 import sql

db_name='module1_qa_'+uuid.uuid4().hex[:10]
connection=psycopg2.connect(host=os.getenv('PGHOST','127.0.0.1'),port=os.getenv('PGPORT','55446'),user=os.getenv('PGUSER','qa_admin'),dbname='postgres')
connection.autocommit=True
with connection.cursor() as cur: cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db_name)))
connection.close()
os.environ['PGDATABASE']=db_name
os.environ['SECRET_KEY']='qa-only-isolated-test-key'
import app as website
from repositories import UserRepository
from validators import RegistrationValidator,parse_date

website.db.execute((ROOT/'schema.sql').read_text(encoding='utf-8'))
website.users.create('Conf2027','Demo77','Администратор портала','8(000)000-00-00','admin@conf.ru','admin')
website.app.config['TESTING']=True
client=website.app.test_client()
results=[]
preview=ROOT.parent/'_qa/module_preview'
preview.mkdir(parents=True,exist_ok=True)

def check(label,condition):
    if not condition: raise AssertionError(label)
    results.append({'check':label,'result':'passed'})

def has(response,text): return text in response.get_data(as_text=True)
def save_page(name,response):
    html=response.get_data(as_text=True)
    for source,target in [('/register','register.html'),('/login','login.html'),('/cabinet','cabinet.html'),('/booking/new','booking_new.html'),('/admin','admin.html')]:
        html=html.replace('href="'+source+'"','href="'+target+'"')
    html=html.replace('href="/"','href="index.html"').replace('/static/','static/')
    (preview/(name+'.html')).write_text(html,encoding='utf-8')

save_page('index',client.get('/'))
save_page('login',client.get('/login'))
check('Guest cannot open cabinet',client.get('/cabinet').status_code==302)
check('Guest cannot open admin',client.get('/admin').status_code==302)
response=client.post('/register',data={})
check('Five missing registration fields show server errors',all(has(response,s) for s in ['Введите логин','Введите пароль','Введите ФИО','Введите телефон','Введите адрес электронной почты']))
save_page('register',response)
valid={'login':'samoylov2027','password':'Testpass2027','full_name':'Самойлов Артем Сергеевич','phone':'8(900)123-45-67','email':'samoylov@example.ru'}
bad=dict(valid,login='ivan',phone='89001234567')
response=client.post('/register',data=bad)
check('Invalid login and phone rejected',has(response,'не менее 6') and has(response,'8(XXX)'))
response=client.post('/register',data=valid,follow_redirects=True)
check('Valid registration stored in PostgreSQL',has(response,'Пользователь создан') and website.users.login_exists(valid['login']))
check('Password stored as a hash',website.db.fetch_one('SELECT password_hash FROM users WHERE login=%s',(valid['login'],))['password_hash']!=valid['password'])
response=client.post('/register',data=valid)
check('Duplicate login rejected',has(response,'Такой логин уже занят'))
response=client.post('/login',data={'login':valid['login'],'password':'wrong'})
check('Wrong password rejected',has(response,'Неверный логин или пароль'))
response=client.post('/login',data={'login':valid['login'],'password':valid['password']},follow_redirects=True)
check('User login opens cabinet',has(response,'Мои заявки'))
check('User cannot modify admin status',client.post('/admin/booking/1/status',data={'status':'Завершено'}).status_code==302 and website.db.fetch_one('SELECT count(*) AS n FROM bookings')['n']==0)
save_page('booking_new',client.get('/booking/new'))
future=(date.today()+timedelta(days=60)).strftime('%d.%m.%Y')
booking={'room_name':'кинозал «премьер»','start_date':future,'payment_method':'Перевод по СБП','participants':'120'}
response=client.post('/booking/new',data=booking,follow_redirects=True)
check('Case insensitive room name and dotted date accepted',has(response,'Заявка отправлена'))
response=client.post('/booking/new',data=dict(booking,room_name='Аудитория «Москва»',participants='20'),follow_redirects=True)
check('Two bookings persisted',website.db.fetch_one('SELECT count(*) AS n FROM bookings')['n']==2)
check('Participants persisted',website.db.fetch_one('SELECT participants FROM bookings ORDER BY id LIMIT 1')['participants']==120)
for label,override,expected in [('Unknown room',{'room_name':'Нет зала'},'Выберите помещение'),('Invalid date',{'start_date':'2027/05/20'},'ДД.ММ.ГГГГ'),('Past date',{'start_date':'01.01.2020'},'в прошлом'),('Bad payment',{'payment_method':'cash'},'Выберите способ оплаты'),('Participants zero',{'participants':'0'},'от 1 до 500'),('Participants overflow',{'participants':'501'},'от 1 до 500'),('Participants fractional',{'participants':'1.5'},'от 1 до 500')]:
    response=client.post('/booking/new',data=dict(booking,**override))
    if not has(response,expected):
        (ROOT/'_qa').mkdir(exist_ok=True)
        (ROOT/'_qa/failed_response.html').write_text(response.get_data(as_text=True),encoding='utf-8')
    check(label+' rejected',has(response,expected) and website.db.fetch_one('SELECT count(*) AS n FROM bookings')['n']==2)
check('Review before completion rejected',has(client.post('/booking/1/review',data={'text':'Рано'},follow_redirects=True),'только после завершения'))
client.get('/logout')
response=client.post('/login',data={'login':'Conf2027','password':'Demo77'},follow_redirects=True)
check('Required admin credentials work',has(response,'Панель администратора') and has(response,'Самойлов'))
response=client.post('/admin/booking/1/status',data={'status':'Завершено'},follow_redirects=True)
check('Admin status persisted in PostgreSQL',website.db.fetch_one('SELECT status FROM bookings WHERE id=1')['status']=='Завершено')
client.post('/admin/booking/1/status',data={'status':'Отменена'})
check('Invalid status cannot overwrite database',website.db.fetch_one('SELECT status FROM bookings WHERE id=1')['status']=='Завершено')
check('Status filter works',len(website.bookings.all('Завершено'))==1)
check('Room filter works',len(website.bookings.all(None,4))==1)
check('Combined filters work',len(website.bookings.all('Завершено',4))==1 and len(website.bookings.all('Новая',4))==0)
save_page('admin',client.get('/admin'))
client.get('/logout')
client.post('/login',data={'login':valid['login'],'password':valid['password']})
response=client.get('/cabinet')
check('Completed booking displays review form',has(response,'Оставить отзыв'))
client.post('/booking/1/review',data={'text':'Удобный зал для конференции'})
check('Review persisted',website.db.fetch_one('SELECT text FROM reviews WHERE booking_id=1')['text']=='Удобный зал для конференции')
client.post('/booking/1/review',data={'text':'Повтор'})
check('Duplicate review does not crash and creates only one row',website.db.fetch_one('SELECT count(*) AS n FROM reviews')['n']==1)
save_page('cabinet',client.get('/cabinet'))
client.post('/booking/2/delete')
check('User can delete own new booking',website.bookings.get(2) is None)
client.post('/booking/1/delete')
check('User cannot delete completed booking',website.bookings.get(1) is not None)
client.get('/logout')
client.post('/login',data={'login':'Conf2027','password':'Demo77'})
client.post('/admin/booking/1/delete')
check('Admin can delete a booking',website.bookings.get(1) is None)
check('Deleting booking cascades review',website.db.fetch_one('SELECT count(*) AS n FROM reviews')['n']==0)
for asset in ['vendor/bootstrap/bootstrap.min.css','vendor/bootstrap/bootstrap.bundle.min.js','css/style.css','js/validation.js','img/logo.svg','img/slide-1.svg','img/slide-2.svg','img/slide-3.svg']:
    check('Asset loads: '+asset,client.get('/static/'+asset).status_code==200)
check('Four tables exist',len(website.db.fetch_all("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))==4)
check('Three foreign keys exist',website.db.fetch_one("SELECT count(*) AS n FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_schema='public'")['n']==3)
check('Schema can be rerun without deleting users',website.db.execute((ROOT/'schema.sql').read_text(encoding='utf-8')) is None and website.users.login_exists(valid['login']))
output={'database':db_name,'postgresql_version':website.db.fetch_one('SELECT version() AS v')['v'],'passed':len(results),'checks':results,'preview_directory':str(preview)}
(ROOT/'TEST_RESULTS.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(results),'database':db_name,'preview':str(preview)},ensure_ascii=False))
