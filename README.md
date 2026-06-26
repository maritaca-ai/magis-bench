# Magis-Bench

Magis-Bench is a benchmark for evaluating LLMs on **magistrate-level** legal writing tasks, drawn from recent Brazilian competitive examinations for judicial positions. It comprises **74 questions** from eight examinations (2023–2025) across federal (TRF1, TRF2, TRF3) and state (TJMS, TJPE, TJGO, TJAM, TJSE) courts: 58 discursive questions and 16 sentence-drafting exercises (8 civil, 8 criminal). Each question comes with the **official evaluation rubric** released by the examination boards.

- Evaluates LLMs on their ability to draft judicial decisions and answer discursive legal questions
- Includes the official scoring rubrics used by the examination boards
- Uses an LLM-as-a-judge with **structured output** (recommended) for auditable, arithmetic-safe scoring
- Single default judge: **`anthropic/claude-opus-4-6`**

> **Looking for the paper results?** The original ICAIL '26 evaluation (4-judge ensemble) is preserved at tag [`paper-icail2026`](https://github.com/maritaca-ai/magis-bench/tree/paper-icail2026). See [Reproducing the paper results](#reproducing-the-paper-results).

## News
- [2026/06] Refreshed leaderboard with a new generation of models, evaluated with a single judge (`anthropic/claude-opus-4-6`) and structured output
- [2026/05] Initial release of the benchmark and evaluation pipeline
- [2026/04] Paper accepted as a **short paper at ICAIL 2026**

## Contents
- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)
- [Structured Output Format](#structured-output-format)
- [Reproducing the paper results](#reproducing-the-paper-results)
- [Citation](#citation)

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
    --model google/gemini-3.1-pro-preview \
    --run-id gemini-3.1-pro-preview \
    --api-base "https://openrouter.ai/api/v1" \
    --api-key "$OPENROUTER_API_KEY" \
    --parallel 20
```

For Sabiá models, point to the Maritaca endpoint:

```bash
python3 gen_api_answer.py \
    --bench-name magis_bench \
    --model sabia-4 \
    --run-id sabia-4 \
    --api-base "https://chat.maritaca.ai/api" \
    --api-key "$MARITACA_API_KEY" \
    --parallel 10
```

**2. Judge the responses with the LLM-as-a-judge** (single judge `anthropic/claude-opus-4-6`, structured output, reasoning effort `high`, temperature 0):

```bash
python3 gen_judgment.py \
    --bench-name magis_bench \
    --judge-model anthropic/claude-opus-4-6 \
    --model-list gemini-3.1-pro-preview \
    --api-base "https://openrouter.ai/api/v1" \
    --api-key "$OPENROUTER_API_KEY" \
    --parallel 10 \
    --structured \
    --reasoning-effort high
```

`--structured` is recommended (see [Structured Output Format](#structured-output-format)). Omit it to fall back to the legacy free-text grading.

**3. Visualize results:**

```bash
python3 show_result.py --bench-name magis_bench \
    --input-file data/magis_bench/model_judgment/anthropic_claude-opus-4-6_single.jsonl
```

## Results

Evaluation on Magis-Bench using `anthropic/claude-opus-4-6` as a single judge with structured output (reasoning effort `high`, temperature 0). Average score is the mean over all 74 questions (0–10). Passing rate is the number of exam sections (out of 24: eight examinations × {discursive, civil sentence, criminal sentence}) where the model's summed score reached the ≥ 6.0 cutoff.

| Rank | Model | Average Score | Passing Rate |
| ---: | --- | ---: | --- |
| 1  | Gemini-3.5-Flash    | 7.10 | 19/24 (79%) |
| 2  | Claude-Opus-4.8     | 6.75 | 17/24 (71%) |
| 3  | Gemini-3.1-Pro      | 6.75 | 16/24 (67%) |
| 4  | GPT-5.4             | 6.10 | 16/24 (67%) |
| 5  | Sabiá-4-Thinking    | 5.57 | 12/24 (50%) |
| 6  | DeepSeek-V4-Pro     | 5.44 | 12/24 (50%) |
| 7  | Sabiá-4             | 5.02 |  8/24 (33%) |
| 8  | GLM-5.2             | 4.38 |  4/24 (17%) |
| 9  | Sabiazinho-4        | 4.29 |  2/24 (8%)  |
| 10 | Kimi-K2.6           | 4.12 |  4/24 (17%) |
| 11 | Qwen3.5-397B        | 4.10 |  3/24 (13%) |
| 12 | Qwen3.5-35B         | 2.64 |  0/24 (0%)  |

Even the strongest models score well below the maximum, underscoring how demanding magistrate-level drafting is.

<details>
<summary><b>Paper results (ICAIL '26, 4-judge ensemble)</b></summary>

<br>

The published paper used an ensemble of four judges (`gpt-5.1`, `gemini-2.5-pro`, `gemini-3-pro-preview`, `claude-4.5-opus`). Mean scores (0–10) across the four judges, over all 74 questions:

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

Inter-judge agreement is near-perfect (Kendall's *W* = 0.984; all pairwise *τ* ≥ 0.897), which motivated moving to a single default judge for routine evaluation.

</details>

## Structured Output Format

When using `--structured`, the judge produces a `JudgmentResult` object (Pydantic) instead of a free-text rating:

```python
class ItemEvaluation(BaseModel):
    item_id: str            # Item identifier
    item_description: str   # Item description from the scoring rubric
    analysis: str           # Detailed analysis comparing the answer with the reference
    score: float            # Score assigned to the item

class JudgmentResult(BaseModel):
    items: List[ItemEvaluation]  # List of evaluated items
    total_score: float           # Total score (sum of all item scores)
```

We recommend the structured format for two reasons:

1. **Auditable** — each rubric item produces a JSON object with `item_id`, `item_description`, `analysis`, and `score`, making individual judgments easy to inspect.
2. **No arithmetic errors** — the total score is computed programmatically by summing item scores, rather than extracted from free text via regex, eliminating the risk of the judge making arithmetic mistakes.

## Reproducing the paper results

The paper's 4-judge ensemble evaluation is preserved at the [`paper-icail2026`](https://github.com/maritaca-ai/magis-bench/tree/paper-icail2026) tag, along with the committed judgment files for all four judges:

```bash
git checkout paper-icail2026
JD=data/magis_bench/model_judgment
python3 show_result.py --bench-name magis_bench --input-file $JD/gpt-5.1_single.jsonl
python3 show_result.py --bench-name magis_bench --input-file $JD/google_gemini-2.5-pro_single.jsonl
python3 show_result.py --bench-name magis_bench --input-file $JD/google_gemini-3-pro-preview_single.jsonl
python3 show_result.py --bench-name magis_bench --input-file $JD/anthropic_claude-4.5-opus-20251124_single.jsonl
```

Averaging the per-judge scores reproduces the table in [Paper results](#results).

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
