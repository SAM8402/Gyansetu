import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
with open('backend/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            k, _, v = line.partition('=')
            os.environ[k.strip()] = v.strip()
key = os.environ.get('GOOGLE_API_KEY', '').split(',')[0].strip()
print(f'key prefix: {key[:12]}...' if key else 'EMPTY KEY', flush=True)
from app.ai.embeddings import get_embeddings
print('import ok', flush=True)
emb = get_embeddings()
print('model created', flush=True)
vec = emb.embed_query('test query')
print(f'OK: dims={len(vec)} first_3={vec[:3]}', flush=True)
