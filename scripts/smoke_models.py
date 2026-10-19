"""Exercise real model integrations using temporary user data."""
import io
import os
import secrets
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix='athena-models-') as temporary:
        os.environ['ATHENA_DATA_DIR']=temporary
        os.environ['ATHENA_JWT_SECRET']=secrets.token_urlsafe(48)
        os.environ['ATHENA_RATE_LIMIT']='0'
        os.environ['ATHENA_ALLOWED_HOSTS']='testserver'
        from fastapi.testclient import TestClient
        from PIL import Image
        from app.api import app
        from app.database.database import engine
        with TestClient(app) as client:
            def register(name):
                response=client.post('/auth/register',json={'username':name,'password':'temporary-test-password-123'})
                assert response.status_code==201,response.text
                return {'Authorization':'Bearer '+response.json()['access_token']}
            alice,bob=register('alice'),register('bob')
            response=client.post('/chat',headers=alice,json={'message':'I live in Jaipur'})
            assert response.status_code==200,response.text
            assert response.json()['memory_action']=='created',response.text
            response=client.post('/chat',headers=alice,json={'message':'Where do I live?'})
            assert response.status_code==200 and 'Jaipur' in response.json()['response'],response.text
            assert client.get('/memories',headers=bob).json()==[]
            print('PASS: real embedding storage, recall and cross-user isolation',flush=True)
            response=client.post('/code/ask',headers=alice,json={'message':'Write a Python function to add two numbers. Keep it short.'})
            assert response.status_code==200 and 'def ' in response.json()['response'],response.text
            print('PASS: local coding model',flush=True)
            picture=io.BytesIO();Image.new('RGB',(128,128),'red').save(picture,'PNG')
            response=client.post('/images',headers=alice,files={'file':('red.png',picture.getvalue(),'image/png')},data={'describe':'true'})
            assert response.status_code==201,response.text
            assert response.json()['caption'],response.text
            print('PASS: local vision model and private image storage',flush=True)
            # Use the supplied video only if explicitly selected by the caller.
            if len(sys.argv)>1:
                with Path(sys.argv[1]).open('rb') as audio:
                    response=client.post('/voice/transcribe',headers=alice,files={'file':('voice.mp4',audio,'video/mp4')})
                assert response.status_code==200 and response.json()['text'],response.text
                print('PASS: local voice transcription',flush=True)
        engine.dispose()


if __name__=='__main__':main()
