"""Fine-tune a small instruction model on TipTune conversations with QLoRA."""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--train-file", type=Path, default=Path("datasets/tiptune_train.jsonl"))
    parser.add_argument("--validation-file", type=Path, default=Path("datasets/tiptune_val.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/tiptune-qlora"))
    parser.add_argument("--epochs", type=float, default=3.0)
    args = parser.parse_args()

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train_file), "test": str(args.validation_file)},
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype="bfloat16",
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=quantization,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=True,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        peft_config=LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules="all-linear",
            task_type="CAUSAL_LM",
        ),
        args=SFTConfig(
            output_dir=str(args.output_dir),
            num_train_epochs=args.epochs,
            learning_rate=2e-4,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=8,
            gradient_checkpointing=True,
            optim="paged_adamw_8bit",
            logging_steps=5,
            eval_strategy="steps",
            eval_steps=20,
            save_strategy="steps",
            save_steps=20,
            save_total_limit=2,
            max_length=1024,
            packing=False,
            report_to="none",
        ),
    )
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
