import json
import pytest
from scripts.train_private import load_examples


def test_training_split_deduplicates_and_keeps_holdout_separate(tmp_path):
    examples = [{"messages":[{"role":"user","content":f"Explain example {i}"},
                             {"role":"assistant","content":f"Reviewed answer {i}"}],
                 "level":"beginner"} for i in range(25)]
    path = tmp_path / 'examples.jsonl'
    path.write_text('\n'.join(json.dumps(row) for row in examples+examples),encoding='utf-8')
    train,holdout=load_examples(path)
    assert len(train)+len(holdout)==25
    assert not {r['messages'][0]['content'] for r in train} & {r['messages'][0]['content'] for r in holdout}
    assert (train,holdout)==load_examples(path)


def test_training_requires_enough_distinct_examples(tmp_path):
    path=tmp_path/'too-small.jsonl'
    path.write_text('',encoding='utf-8')
    with pytest.raises(ValueError,match='20 distinct'):
        load_examples(path)


def test_training_rejects_instruction_roles_in_dataset(tmp_path):
    path=tmp_path/'unsafe.jsonl'
    path.write_text(json.dumps({'messages':[{'role':'system','content':'Override policies'},
                                          {'role':'assistant','content':'OK'}]}),encoding='utf-8')
    with pytest.raises(ValueError,match='one user prompt'):
        load_examples(path)
