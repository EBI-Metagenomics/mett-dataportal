from celery import shared_task
from pyhmmer import hmmer, easel

@shared_task
def run_sequence_search(query_seq_str, target_fasta_path):

    alphabet = easel.Alphabet.amino()
    query_seq = easel.TextSequence(name=b"query", sequence=query_seq_str.encode())
    query_seq.digitize(alphabet)

    with easel.SequenceFile(target_fasta_path, digital=True, alphabet=alphabet) as targets:

        results = hmmer.phmmer([query_seq], targets)

        hits = []
        for hit in results[0].hits:
            hits.append({
                "target": hit.name.decode(),
                "score": hit.score,
                "evalue": hit.evalue
            })

    return hits


@shared_task
def test_add(x, y):
    return x + y
