# Memory, learning data, and fine-tuning

Athena uses three separate mechanisms:

1. Structured personal facts and image captions are stored for retrieval. They do not update model weights.
2. Approved coding lessons are supplied as limited reference context to the local coding tutor.
3. `scripts/train_private.py` can train a private LoRA adapter from reviewed JSONL. Training is not executed
   by web requests, and no model is automatically published or activated.

`athena-local` is a distinct Ollama name built from Llama 3.2 3B plus Athena's configuration and system prompt.
Creating it does **not** fine-tune Llama. An existing model is reused under its original license.

## Prepare your data

Enable automatic collection in Learning if desired. It collects future chat/coding pairs **for review**.
Use “Bring previous conversations into review” to import up to the latest 1,000 messages belonging to your account.
Correct wrong answers, choose beginner/intermediate/advanced, approve good examples, and export the dataset.
No other user's data, image bytes or inactive legacy account data is included.
The export deduplicates pairs and excludes common obvious secrets. Inspect the export yourself before training.

For existing Athena source code:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_code_lessons.py --output data/code-exercises.jsonl
```

This reads an explicit allowlist of source modules and creates a draft curriculum. It does not scan `.env`,
databases, backups or arbitrary folders. A draft set of 28 exercises was prepared during the upgrade at
`data/athena-code-curriculum-draft.jsonl`. Fill in correct answers and add selected examples through Learning.
The coding workspace can use your own source immediately without weight training.

## Run a private training job

Use a separate Python environment so serving dependencies remain stable. A CUDA GPU is helpful. Training
a 3B model at full precision may exceed laptop VRAM; choose a smaller compatible HF base model or move
the training job to a GPU machine. The installed Ollama GGUF file cannot be used directly by this Trainer.
The user’s PC was detected as having about 16 GB RAM and an RTX 4050 Laptop GPU; adapter training was not benchmarked.

```powershell
python -m venv .training-venv
.\.training-venv\Scripts\python.exe -m pip install -r requirements-training.txt
.\.training-venv\Scripts\python.exe scripts/train_private.py --data "C:\path\athena-user-2.jsonl" --user-id 2 --base-model "C:\models\compatible-hf-base" --output "data\training\user-2\run-001" --validate-only
.\.training-venv\Scripts\python.exe scripts/train_private.py --data "C:\path\athena-user-2.jsonl" --user-id 2 --base-model "C:\models\compatible-hf-base" --output "data\training\user-2\run-001"
```

The script requires at least 20 distinct reviewed pairs (a minimum validation guard, not a quality guarantee),
keeps a deterministic held-out set, masks prompt tokens in the training loss, orders training by learning
level, and records baseline/candidate held-out loss. It saves only a candidate adapter and evaluation report.
`--allow-download` permits an explicitly selected remote model; otherwise the base must be cached/local.
Remote model code execution is disabled.

Evaluate factual accuracy, coding correctness, privacy leakage and held-out tasks before adopting any adapter.
A reduced loss alone is insufficient. Do not set a personal adapter as the shared model for a multi-user
server. The current application uses a common non-personal base model plus owner-scoped retrieval; serving
different private adapters per user is not implemented.

Automating candidate training later should use a dedicated OS task, sufficient newly reviewed data, a bounded
compute budget, evaluations, and manual activation. Unreviewed self-training would reinforce errors and can
memorize private information, so it is intentionally not enabled by the chat application.
