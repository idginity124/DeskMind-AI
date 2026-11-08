from deskmind import Index, chunk_text, answer, grounded_prompt

def test_chunk_overlap():
    assert chunk_text('a b c d e',size=3,overlap=1)==['a b c','c d e','e']
def test_search_relevance():
    idx=Index([{'id':'a#chunk-0','source':'a','text':'Incident response has containment and recovery steps.'},{'id':'b#chunk-0','source':'b','text':'Neural networks use gradient descent.'}])
    assert idx.search('containment incident')[0]['id']=='a#chunk-0'
def test_abstain_without_evidence():
    idx=Index([{'id':'x','source':'x','text':'Cats are animals.'}])
    assert not answer(idx,'satellite orbital physics')['sources']
def test_prompt_citations():
    assert '[a#chunk-0]' in grounded_prompt('question',[{'id':'a#chunk-0','text':'example'}])
