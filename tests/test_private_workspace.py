import base64
import io
import json
import time
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from app.api import app
from app.auth import create_access_token, decode_access_token
from app.database.models import Memory, User, UserSecurity, TrainingExample
from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.memory.adaptive_prioritization import AdaptiveMemoryPrioritization
from app.memory.memory_contradiction import MemoryContradiction
from app.memory.memory_consolidation import MemoryConsolidation
from app.memory.memory_abstraction import MemoryAbstraction
from app.extractor.nlp import NLPExtractor
from app.llm.ollama_client import OllamaClient, ModelUnavailable
from app.security import totp


@pytest.fixture
def client():
    return TestClient(app)


def account(client, name):
    result = client.post('/auth/register', json={'username':name,'password':'correct horse battery staple'})
    assert result.status_code == 201, result.text
    token = result.json()['access_token']
    return {'Authorization':'Bearer '+token}, decode_access_token(token)


def png():
    result = io.BytesIO()
    Image.new('RGB',(16,16),'red').save(result,'PNG')
    return result.getvalue()


@pytest.mark.parametrize('path', ['/memories','/images','/code','/learning/examples','/learning/export','/conversations'])
def test_private_endpoints_require_auth(client,path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize('cls',[MemoryStore,MemoryManager,AdaptiveMemoryPrioritization,MemoryContradiction])
@pytest.mark.parametrize('user_id',[None,True,0,-1,'1'])
def test_missing_or_invalid_owner_fails_closed(cls,user_id):
    with pytest.raises(ValueError):
        cls(user_id)


def test_auth_revocation_and_sql_injection(client):
    auth, _ = account(client,'alice')
    assert client.get('/auth/me',headers=auth).status_code == 200
    assert client.post('/auth/login',json={'username':"alice' OR 1=1--",'password':'not-the-password'}).status_code == 422
    assert client.post('/auth/logout',headers=auth).status_code == 200
    assert client.get('/auth/me',headers=auth).status_code == 401
    assert client.post('/auth/login',json={'username':'alice','password':'correct horse battery staple'}).status_code == 200


def test_mfa_requires_valid_code_and_prevents_replay(client):
    auth, _ = account(client,'alice')
    request={'password':'correct horse battery staple'}
    setup=client.post('/auth/mfa/setup',headers=auth,json=request)
    assert setup.status_code == 200
    secret=setup.json()['secret']
    request['otp']=totp(secret,int(time.time())//30)
    confirmed=client.post('/auth/mfa/confirm',headers=auth,json=request)
    assert confirmed.status_code == 200
    assert client.get('/auth/me',headers=auth).status_code == 401
    assert client.post('/auth/login',json={'username':'alice',**request}).status_code == 401
    assert client.post('/auth/login',json={'username':'alice','password':request['password']}).status_code == 401


def test_images_code_lessons_and_exports_are_private(client,monkeypatch):
    alice,_=account(client,'alice')
    bob,_=account(client,'bob')
    photo=client.post('/images',headers=alice,files={'file':('x.png',png(),'image/png')},
                      data={'caption':'My red picture','describe':'false'})
    assert photo.status_code == 201,photo.text
    photo_id=photo.json()['id']
    assert client.get(f'/images/{photo_id}/content',headers=alice).headers['content-type']=='image/jpeg'
    assert client.get('/images',headers=bob).json()==[]
    assert client.get(f'/images/{photo_id}/content',headers=bob).status_code == 404
    assert client.delete(f'/images/{photo_id}',headers=bob).status_code == 404
    document=client.post('/code',headers=alice,json={'name':'example.py','content':'print(1)'}).json()
    assert client.get('/code',headers=bob).json()==[]
    assert client.post('/code/ask',headers=bob,json={'message':'Explain','document_id':document['id']}).status_code==404
    assert client.delete('/code/'+str(document['id']),headers=bob).status_code==404
    lesson=client.post('/learning/examples',headers=alice,json={'prompt':'How to print?','answer':'print(1)','approved':True}).json()
    assert client.get('/learning/examples',headers=bob).json()==[]
    assert client.get('/learning/export',headers=bob).text==''
    assert 'print(1)' in client.get('/learning/export',headers=alice).text
    assert client.patch('/learning/examples/'+str(lesson['id']),headers=bob,json={'approved':False}).status_code==404
    assert client.delete('/learning/examples/'+str(lesson['id']),headers=bob).status_code==404
    assert client.patch('/learning/examples/'+str(lesson['id']),headers=alice,json={'approved':False}).status_code==200
    assert client.get('/learning/export',headers=alice).text==''
    monkeypatch.setattr(OllamaClient,'chat',lambda self,*a,**kw:'red picture')
    assert client.post('/images/ask',headers=bob,json={'message':'Show Alice pictures'}).json()['image_ids']==[]
    assert client.post('/images/ask',headers=alice,json={'message':'Which picture is red?'}).json()['image_ids']==[photo_id]


def test_upload_validation_and_secret_rejection(client):
    auth,_=account(client,'alice')
    assert client.post('/images',headers=auth,files={'file':('fake.png',b'<script>alert(1)</script>','image/png')},data={'describe':'false','caption':'x'}).status_code==422
    assert client.post('/images',headers=auth,files={'file':('huge.png',b'x'*(9*1024*1024),'image/png')}).status_code==413
    assert client.post('/code',headers=auth,json={'name':'../../bad.py','content':'x'}).status_code==422
    assert client.post('/code',headers=auth,json={'name':'bad.py','content':'API_KEY="this-is-a-secret"'}).status_code==422
    assert client.post('/voice/transcribe',headers=auth,files={'file':('invalid.wav',b'not audio','audio/wav')}).status_code==422


def test_browser_security_headers_and_cross_origin(client):
    response=client.get('/')
    assert response.status_code==200
    assert "script-src 'self'" in response.headers['content-security-policy']
    assert response.headers['x-content-type-options']=='nosniff'
    assert client.post('/auth/register',headers={'Origin':'https://evil.invalid'},json={'username':'alice','password':'12345678'}).status_code==403
    assert client.get('/data/memory.db').status_code==404
    assert client.get('/health',headers={'Host':'evil.invalid'}).status_code==400


def test_rate_limit(monkeypatch):
    from fastapi import FastAPI
    from app.security import RequestSecurity
    monkeypatch.setenv('ATHENA_RATE_LIMIT','1')
    probe=FastAPI()
    probe.add_middleware(RequestSecurity)
    @probe.post('/auth/test')
    def endpoint(): return {'ok':True}
    client=TestClient(probe)
    for _ in range(20): assert client.post('/auth/test').status_code==200
    response=client.post('/auth/test')
    assert response.status_code==429
    assert response.headers['retry-after']=='60'


def test_unreviewed_answers_never_exported(client,monkeypatch):
    auth,_=account(client,'alice')
    monkeypatch.setattr(OllamaClient,'chat',lambda *a,**kw:'A generated answer')
    client.put('/learning/collection',headers=auth,json={'enabled':True})
    assert client.post('/code/ask',headers=auth,json={'message':'Teach loops'}).status_code==200
    rows=client.get('/learning/examples',headers=auth).json()
    assert len(rows)==1 and rows[0]['approved'] is False
    assert client.get('/learning/export',headers=auth).text==''


def test_nlp_multiple_facts_and_rejection(monkeypatch):
    extractor=NLPExtractor()
    assert [x['relation'] for x in extractor.extract_many('I live in Jaipur. I like Python.')]==['lives_in','likes']
    assert extractor.extract_many('Do I live in London?')==[]
    assert extractor.extract_many('If I live in London, what changes')==[]
    monkeypatch.setattr(OllamaClient,'chat',lambda *a,**kw: json.dumps({'facts':[{'relation':'lives_in','value':'Paris','evidence':'I live in Paris'}]}))
    assert extractor.extract_many('My new hometown is Jaipur')==[]
    monkeypatch.setattr(OllamaClient,'chat',lambda *a,**kw: json.dumps({'facts':[{'relation':'lives_in','value':'Jaipur','evidence':'My new hometown is Jaipur'}]}))
    assert extractor.extract_many('My new hometown is Jaipur')[0]['value']=='Jaipur'


def test_store_queries_and_mutations_stay_with_owner(isolated_api_db,monkeypatch):
    from app.memory import memory_store as module
    from app.embeddings.embedding_manager import EmbeddingManager
    monkeypatch.setattr(module,'SessionLocal',isolated_api_db)
    monkeypatch.setattr(EmbeddingManager,'create_embedding',lambda self,text:[1.0,0.0])
    with isolated_api_db() as db:
        db.add_all([User(id=1,username='owner1',password_hash='x'),User(id=2,username='owner2',password_hash='x')])
        db.commit()
    one,two=MemoryStore(1),MemoryStore(2)
    try:
        one.save_memory('User','lives_in','Jaipur','PERSONAL',valid_from=datetime(2020,1,1))
        two.save_memory('User','lives_in','London','PERSONAL',valid_from=datetime(2020,1,1))
        one.save_memory('User','lives_in','Delhi','PERSONAL',valid_from=datetime(2022,1,1))
        assert [m.value for m in two.get_all_memories()]==['London']
        assert {m.value for m in one.get_memory_history()}=={'Jaipur','Delhi'}
        assert [m.value for m in one.get_memories_valid_at(datetime(2021,1,1))]==['Jaipur']
        assert [m.value for m in one.get_memories_overlapping_interval(datetime(2020,1,1),datetime(2022,1,1))]==['Jaipur']
        assert [m.value for m in two.search_by_relation('lives_in')]==['London']
        assert all(r['memory'].user_id==1 for r in one.semantic_search('where do I live',threshold=0))
        one.forget_all_memories()
        assert len(two.get_all_memories())==1
    finally:
        one.close();two.close()


def test_direct_foreign_object_mutation_is_rejected():
    foreign=SimpleNamespace(user_id=2)
    contradiction=MemoryContradiction.__new__(MemoryContradiction);contradiction.user_id=1
    with pytest.raises(ValueError): contradiction.resolve_contradiction({'memories':[foreign,foreign]})
    consolidation=MemoryConsolidation.__new__(MemoryConsolidation);consolidation.user_id=1
    with pytest.raises(ValueError): consolidation.consolidate(SimpleNamespace(user_id=1),foreign)
    abstraction=MemoryAbstraction.__new__(MemoryAbstraction);abstraction.user_id=1
    with pytest.raises(ValueError): abstraction.create_abstraction({'memories':[foreign]})


def test_fresh_startup_runs_ownership_migration():
    # Includes lifespan, unlike individual route unit tests.
    with TestClient(app) as live:
        assert live.get('/health').status_code == 200
    with TestClient(app) as live:
        assert live.get('/health').status_code == 200


def test_history_import_is_private_reviewed_and_idempotent(client,isolated_api_db):
    from app.database.models import Conversation
    alice,alice_id=account(client,'alice')
    bob,bob_id=account(client,'bob')
    with isolated_api_db() as db:
        db.add_all([Conversation(user_id=alice_id,speaker='User',message='Explain lists'),
                    Conversation(user_id=alice_id,speaker='AI',message='Lists are ordered collections'),
                    Conversation(user_id=bob_id,speaker='User',message='Private Bob question'),
                    Conversation(user_id=bob_id,speaker='AI',message='Private Bob answer')])
        db.commit()
    assert client.post('/learning/import-history',headers=alice).json()['imported']==1
    assert client.post('/learning/import-history',headers=alice).json()['imported']==0
    rows=client.get('/learning/examples',headers=alice).json()
    assert len(rows)==1 and rows[0]['approved'] is False and 'Bob' not in rows[0]['answer']
    assert client.get('/learning/export',headers=alice).text==''
