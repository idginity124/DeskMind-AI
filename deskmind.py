"""Small, inspectable, local-first retrieval-augmented document Q&A baseline."""
from __future__ import annotations
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

TOKEN = re.compile(r"\b\w+\b", re.UNICODE)
def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.casefold())

def chunk_text(text: str, size: int = 120, overlap: int = 25) -> list[str]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("size must be positive; overlap must be smaller than size")
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size - overlap) if words[i:i + size]]

class Index:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.freq = [Counter(tokens(d['text'])) for d in docs]
        self.df = Counter(word for freq in self.freq for word in freq)
        self.n = len(docs)
    @classmethod
    def from_dir(cls, folder: str, size: int = 120, overlap: int = 25):
        root = Path(folder)
        if not root.is_dir():
            raise FileNotFoundError(f"Documents directory not found: {root}")
        docs = []
        for p in sorted(root.rglob('*')):
            if p.is_file() and p.suffix.lower() in {'.txt', '.md'}:
                content = p.read_text(encoding='utf-8')
                for i, chunk in enumerate(chunk_text(content, size, overlap)):
                    docs.append({'id':f'{p.relative_to(root)}#chunk-{i}', 'source':str(p.relative_to(root)), 'text':chunk})
        return cls(docs)
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        q = Counter(tokens(query))
        if not q or top_k < 1:
            return []
        scores = []
        for doc, freq in zip(self.docs, self.freq):
            score = sum((1 + math.log(freq[t])) * math.log(1 + (self.n + 1) / (self.df[t] + 1)) * qn for t, qn in q.items() if freq[t])
            if score > 0:
                scores.append({**doc, 'score': round(score, 5)})
        return sorted(scores, key=lambda x: (-x['score'], x['id']))[:top_k]

def grounded_prompt(question: str, hits: list[dict]) -> str:
    context = '\n\n'.join(f"[{h['id']}] {h['text']}" for h in hits)
    return ("Answer using ONLY the context below. Cite sources using [source#chunk]. "
            "If the context does not answer the question, say 'I don't know based on these documents'.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")

def ollama_generate(prompt: str, model: str, endpoint: str = 'http://127.0.0.1:11434/api/generate') -> str:
    payload = json.dumps({'model':model,'prompt':prompt,'stream':False}).encode('utf-8')
    req = Request(endpoint, data=payload, headers={'Content-Type':'application/json'}, method='POST')
    with urlopen(req, timeout=120) as response:
        return json.load(response)['response']

def answer(index: Index, question: str, model: str | None = None) -> dict:
    hits = index.search(question)
    if not hits:
        return {'answer':'I don\'t know based on these documents.', 'sources':[]}
    if model:
        text = ollama_generate(grounded_prompt(question, hits), model)
    else:
        text = 'Retrieved evidence (use --model to generate an answer): ' + hits[0]['text']
    return {'answer':text, 'sources':[{'id':h['id'],'score':h['score']} for h in hits]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('question');p.add_argument('--docs',default='examples/docs');p.add_argument('--model',help='Installed Ollama model, e.g. qwen2.5:3b')
    a=p.parse_args()
    print(json.dumps(answer(Index.from_dir(a.docs),a.question,a.model),indent=2,ensure_ascii=False))
if __name__=='__main__': main()
