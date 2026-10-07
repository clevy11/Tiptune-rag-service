"""Interactively test the TipTune QLoRA adapter on an NVIDIA GPU."""

from __future__ import annotations

import argparse

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, BitsAndBytesConfig

SYSTEM_PROMPT = (
    "You are TipTune Support, the friendly assistant for TipTune "
    "(tiptune.space), a real-time song request platform for DJs, artists and "
    "live events in Kigali and beyond. Answer questions about how TipTune works "
    "in a casual, warm, helpful tone. Keep answers clear and short. If you don't "
    "know something, don't guess: point the person to TipTune support on "
    "WhatsApp/phone 0792548195 or email titunerw@gmail.com."
)


def answer(model, tokenizer, question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=180,
            do_sample=False,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = generated[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def load_adapter(adapter: str):
    if not torch.cuda.is_available():
        raise RuntimeError("An NVIDIA GPU is required to load this QLoRA adapter.")

    tokenizer = AutoTokenizer.from_pretrained(adapter)
    model = AutoPeftModelForCausalLM.from_pretrained(
        adapter,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
        device_map="auto",
        torch_dtype="auto",
    )
    model.eval()
    return model, tokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default="outputs/tiptune-qlora")
    args = parser.parse_args()
    model, tokenizer = load_adapter(args.adapter)
    print("TipTune adapter loaded. Type 'quit' to exit.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if question:
            print(f"\nTipTune Support: {answer(model, tokenizer, question)}")


if __name__ == "__main__":
    main()
