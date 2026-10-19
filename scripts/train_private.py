"""LoRA training on ONE owner's reviewed JSONL; never auto-publishes a model.

Run in a dedicated training environment. See docs/TRAINING.md.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def load_examples(path):
    rows, seen = [], set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        messages = row.get("messages", [])
        if len(messages) != 2 or [m.get("role") for m in messages] != ["user", "assistant"]:
            raise ValueError("Each example must contain one user prompt and one reviewed assistant answer.")
        if any(not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
            raise ValueError("Empty or invalid example.")
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        if digest not in seen:
            seen.add(digest)
            rows.append(row)
    if len(rows) < 20:
        raise ValueError("Provide at least 20 distinct reviewed examples before training.")
    # Stable holdout; duplicate examples cannot leak into the validation set.
    rows.sort(key=lambda r: hashlib.sha256(json.dumps(r["messages"], sort_keys=True).encode()).hexdigest())
    count = max(2, len(rows)//10)
    return rows[count:], rows[:count]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--base-model", required=True, help="Local HF model directory or a model you have permission to download")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New, private output directory")
    parser.add_argument("--epochs", type=int, default=1, choices=range(1, 6))
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.user_id < 1:
        parser.error("user-id must be positive")
    train, validation = load_examples(args.data)
    print(f"Training: {len(train)} examples; holdout: {len(validation)} examples; owner: {args.user_id}")
    if args.validate_only:
        return
    if args.output.exists():
        parser.error("output directory must not already exist")
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, local_files_only=not args.allow_download, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.base_model, local_files_only=not args.allow_download,
                                                trust_remote_code=False, torch_dtype=torch.float32)
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", r=8, lora_alpha=16,
                                            lora_dropout=0.05, target_modules="all-linear"))
    model.config.use_cache = False

    def encode(row):
        prompt = f"User: {row['messages'][0]['content']}\nAssistant: "
        prefix = tokenizer.encode(prompt, add_special_tokens=False)[:384]
        answer = tokenizer.encode(row['messages'][1]['content']+tokenizer.eos_token, add_special_tokens=False)[:512-len(prefix)]
        return {"input_ids": prefix+answer, "attention_mask": [1]*(len(prefix)+len(answer)),
                "labels": [-100]*len(prefix)+answer}

    train.sort(key=lambda row: {"beginner":0,"intermediate":1,"advanced":2}.get(row.get("level"),0))
    # A sequential sampler makes the beginner -> advanced curriculum explicit.
    class CurriculumTrainer(Trainer):
        def _get_train_sampler(self, train_dataset=None):
            return torch.utils.data.SequentialSampler(train_dataset if train_dataset is not None else self.train_dataset)

    trainer = CurriculumTrainer(model=model,
        args=TrainingArguments(output_dir=str(args.output), num_train_epochs=args.epochs,
            per_device_train_batch_size=1, per_device_eval_batch_size=1, gradient_accumulation_steps=8,
            learning_rate=0.0001, report_to="none", save_strategy="no", seed=42, dataloader_num_workers=0),
        train_dataset=Dataset.from_list([encode(row) for row in train]),
        eval_dataset=Dataset.from_list([encode(row) for row in validation]),
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100))
    before = trainer.evaluate()["eval_loss"]
    trainer.train()
    after = trainer.evaluate()["eval_loss"]
    acceptable = math.isfinite(after) and after < before
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"user_id":args.user_id, "base_model":args.base_model, "baseline_loss":before,
              "candidate_loss":after, "improved_holdout_loss":acceptable,
              "status":"candidate_requires_manual_quality_and_privacy_review", "auto_activated":False}
    (args.output/"evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    model.save_pretrained(args.output/"adapter")
    tokenizer.save_pretrained(args.output/"adapter")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
