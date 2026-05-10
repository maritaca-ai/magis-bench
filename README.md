# Magis-Bench

Magis-Bench is a benchmark for evaluating LLMs on **magistrate-level** legal writing tasks, drawn from recent Brazilian competitive examinations for judicial positions. It comprises **74 questions** from eight examinations (2023–2025) across federal (TRF1, TRF2, TRF3) and state (TJMS, TJPE, TJGO, TJAM, TJSE) courts: 58 discursive questions and 16 sentence-drafting exercises (8 civil, 8 criminal). Each question comes with the **official evaluation rubric** released by the examination boards.

## News
- [2026/04] Paper accepted as a **short paper at ICAIL 2026**
- [2026/05] Initial release of the benchmark and evaluation pipeline

## Installation

```bash
git clone https://github.com/maritaca-ai/magis-bench.git
cd magis-bench
pip install -e .
```

## Usage

The pipeline has three steps: generate model answers, judge them, and view results.

**1. Generate model responses** (via OpenRouter, OpenAI, or Maritaca AI APIs):

```bash
python3 gen_api_answer.py \
    --bench-name magis_bench \
    --model google/gemini-3-pro-preview \
    --run-id gemini-3-pro-preview \
    --api-base "https://openrouter.ai/api/v1" \
    --api-key "$OPENROUTER_API_KEY" \
    --parallel 20
```

**2. Judge the responses with an LLM-as-a-judge** (rubric-grounded; reasoning effort `high`, temperature 0):

```bash
python3 gen_judgment.py \
    --bench-name magis_bench \
    --judge-model openai/gpt-5.1 \
    --model-list gemini-3-pro-preview \
    --api-base "https://openrouter.ai/api/v1" \
    --api-key "$OPENROUTER_API_KEY" \
    --parallel 10 \
    --structured \
    --reasoning-effort high
```

To reproduce the paper's multi-judge evaluation, repeat with each of: `openai/gpt-5.1`, `google/gemini-2.5-pro`, `google/gemini-3-pro-preview`, `anthropic/claude-4.5-opus`.

**3. Visualize results:**

```bash
python3 show_result.py --bench-name magis_bench --judge-model openai/gpt-5.1
```

## Results

Mean scores (0–10) across the four judges, over all 74 questions:

| Rank | Model | GPT-5.1 | Gemini-2.5-Pro | Gemini-3-Pro | Claude-4.5-Opus | **AVG** |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1  | Gemini-3-Pro-Preview          | 6.45 | 7.29 | 7.43 | 6.69 | **6.97** |
| 2  | Gemini-3-Flash-Preview        | 6.08 | 6.86 | 7.29 | 6.46 | **6.67** |
| 3  | Claude-4.5-Opus               | 5.89 | 6.74 | 6.97 | 6.24 | **6.46** |
| 4  | GPT-5.1                       | 6.06 | 6.60 | 6.49 | 5.75 | **6.23** |
| 5  | Gemini-2.5-Pro                | 5.77 | 6.37 | 6.67 | 5.91 | **6.18** |
| 6  | Claude-4.5-Sonnet             | 5.30 | 5.86 | 5.63 | 5.39 | **5.55** |
| 7  | GPT-4.1                       | 4.68 | 5.39 | 5.73 | 5.01 | **5.20** |
| 8  | Sabiá-4                       | 4.46 | 5.26 | 5.60 | 4.79 | **5.03** |
| 9  | Sabiá-3.1                     | 3.98 | 4.77 | 4.76 | 4.15 | **4.41** |
| 10 | DeepSeek-V3.2                 | 4.04 | 4.70 | 4.90 | 3.73 | **4.34** |
| 11 | Kimi-K2.5                     | 3.97 | 4.43 | 4.43 | 3.83 | **4.17** |
| 12 | Kimi-K2-Thinking              | 3.91 | 4.26 | 4.59 | 3.80 | **4.14** |
| 13 | GPT-5-Mini                    | 3.62 | 4.34 | 4.66 | 3.70 | **4.08** |
| 14 | Sabiazinho-4                  | 3.65 | 4.39 | 4.49 | 3.70 | **4.06** |
| 15 | Qwen3-235B-Thinking           | 3.48 | 4.21 | 4.60 | 3.74 | **4.00** |
| 16 | Qwen3-235B-Instruct           | 3.40 | 4.09 | 4.22 | 3.64 | **3.84** |
| 17 | GPT-4.1-Mini                  | 3.62 | 4.06 | 4.29 | 3.38 | **3.84** |
| 18 | Sabiazinho-3                  | 3.11 | 3.13 | 3.50 | 2.83 | **3.14** |
| 19 | Qwen3-30B-Instruct            | 2.59 | 3.24 | 3.28 | 2.51 | **2.91** |
| 20 | Qwen2.5-72B-Instruct          | 2.58 | 2.83 | 2.92 | 2.16 | **2.62** |
| 21 | Qwen3-30B-Thinking            | 2.33 | 2.55 | 2.50 | 2.01 | **2.35** |
| 22 | Qwen2.5-14B-Instruct          | 2.10 | 1.95 | 2.30 | 1.82 | **2.04** |
| 23 | Qwen3-8B                      | 1.86 | 1.81 | 2.13 | 1.46 | **1.82** |

Even the best model scores below 70% of the maximum. Inter-judge agreement is near-perfect (Kendall's *W* = 0.984; all pairwise *τ* ≥ 0.897).

## Citation

```bibtex
@inproceedings{magisbench2026,
  author    = {Pires, Ramon and Sales Almeida, Thales and Larcher Junior, Celio and Bon{\'a}s, Giovana and Abonizio, Hugo and Piau, Marcos and Malaquias Junior, Roseval and Laitz, Thiago and Nogueira, Rodrigo},
  title     = {Magis-Bench: Evaluating LLMs on Magistrate-Level Legal Tasks},
  booktitle = {Proceedings of the Twenty-First International Conference on Artificial Intelligence and Law (ICAIL '26)},
  year      = {2026},
  note      = {Short paper. To appear.}
}
```
