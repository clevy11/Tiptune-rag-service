# TipTune support assistant

## Current approach: RAG

The primary implementation is a retrieval-augmented generation (RAG) backend:
it retrieves current, reviewed TipTune support information from
`knowledge_base/` and the existing `datasets/` support Q&A before asking a
hosted model to reply. Start with
[docs/rag_setup.md](docs/rag_setup.md).

Fine-tuning material remains in this repository as a learning experiment, but
it is not the recommended production source of TipTune product facts.

This project fine-tunes a small open-weight chat model to write short, warm
TipTune support replies for the TipTune website. It does **not** put secrets,
datasets, or model weights into source control.

## Approach

Use QLoRA: the base model remains frozen and training produces a compact LoRA
adapter. The initial base model is `Qwen/Qwen2.5-3B-Instruct`; it is a practical
learning-sized instruction model. Review its licence before commercial release.

Fine-tuning teaches reply style and recurring support flows. It is not a safe
source of truth for changing product facts. RAG can be added later for current
FAQs and policies.

## Prerequisites

- An NVIDIA GPU runtime (Google Colab is a good first option) with roughly 8 GB
  or more VRAM.
- Python 3.10+.
- A Hugging Face account/token if the chosen base model requires one.

OpenRouter is useful to compare hosted models during evaluation, but an
OpenRouter key does not train this adapter. Keep it in `.env`, never in browser
JavaScript or Git.

## Run a first experiment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/validate_dataset.py datasets/tiptune_train.jsonl datasets/tiptune_val.jsonl
python src/train_qlora.py --epochs 3
```

On Colab, upload or clone this repository, install the requirements, and run
the same two Python commands in a GPU notebook cell. Do not attempt the final
training command on CPU.

If you use Jupyter, open [notebooks/tiptune_qlora.ipynb](notebooks/tiptune_qlora.ipynb)
from the repository root and run cells top to bottom. Select a Python kernel
with access to an NVIDIA GPU. The notebook checks for CUDA before it installs
packages or starts training.

The validator checks the source data before training and stops if it finds an
invalid conversation or likely character-encoding corruption. Repair and review
the source answers first; do not blindly transform support policies. Once
validation passes, the adapter and tokenizer are written to
`outputs/tiptune-qlora/`.

## Test the trained adapter

Use the same GPU-enabled Jupyter kernel that trained the model. Run:

```powershell
python src/chat_with_adapter.py
```

Ask one question at a time; enter `quit` to end the session. Start with the
prompts in [docs/evaluation_prompts.md](docs/evaluation_prompts.md). This is a
manual quality check: do not put the adapter into the website until its answers
are reviewed, especially for money, privacy, and unknown-policy questions.

If the notebook says that 4-bit quantization needs `bitsandbytes`, run the
following in a fresh cell, restart the Jupyter kernel, and run the test cell
again:

```python
%pip install -U "bitsandbytes>=0.46.1"
```

## Evaluation before website use

Keep the 20 validation conversations out of training. Test the adapter against:

- questions it has seen paraphrased differently;
- unknown or unsupported payment/payout questions;
- adversarial prompts asking it to invent policies; and
- escalation behavior to TipTune support.

Manually approve every answer involving money, account access, or payments.
