"""
Usage:
python gen_judgment.py --model-list [LIST-OF-MODEL-ID] --parallel [num-concurrent-api-call] --mode [single|pairwise-baseline|pairwise-all]
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

import numpy as np
from tqdm import tqdm
from openai import OpenAI

from common import (
    load_questions,
    load_model_answers,
    load_judge_prompts,
    check_data,
    play_a_match_pair,
    play_a_match_single,
    get_model_list,
    Judge,
    MatchPair,
    MatchSingle,
    NEED_REF_CATS,
    MAGIS_CATS,
)


def make_match(
    questions,
    models,
    model_answers,
    judge,
    baseline_model,
    ref_answers=None,
    multi_turn=False,
):
    matches = []
    for q in questions:
        if multi_turn and len(q["turns"]) != 2:
            continue
        for i in range(len(models)):
            q_id = q["question_id"]
            m_1 = models[i]
            m_2 = baseline_model
            if m_1 == m_2:
                continue
            a_1 = model_answers[m_1][q_id]
            a_2 = model_answers[baseline_model][q_id]
            if ref_answers is not None:
                ref = ref_answers["guidelines"][q_id]
                match = MatchPair(
                    dict(q),
                    m_1,
                    m_2,
                    a_1,
                    a_2,
                    judge,
                    ref_answer=ref,
                    multi_turn=multi_turn,
                )
            else:
                match = MatchPair(
                    dict(q), m_1, m_2, a_1, a_2, judge, multi_turn=multi_turn
                )
            matches.append(match)
    return matches


def make_match_all_pairs(
    questions,
    models,
    model_answers,
    judge,
    baseline_model=None,
    ref_answers=None,
    multi_turn=False,
):
    matches = []
    for q in questions:
        if multi_turn and len(q["turns"]) != 2:
            continue
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                q_id = q["question_id"]
                m_1 = models[i]
                m_2 = models[j]
                a_1 = model_answers[m_1][q_id]
                a_2 = model_answers[m_2][q_id]
                if ref_answers is not None:
                    ref = ref_answers["guidelines"][q_id]
                    match = MatchPair(
                        dict(q),
                        m_1,
                        m_2,
                        a_1,
                        a_2,
                        judge,
                        ref_answer=ref,
                        multi_turn=multi_turn,
                    )
                else:
                    match = MatchPair(
                        dict(q), m_1, m_2, a_1, a_2, judge, multi_turn=multi_turn
                    )
                matches.append(match)
    return matches


def make_match_single(
    questions,
    models,
    model_answers,
    judge,
    baseline_model=None,
    ref_answers=None,
    multi_turn=False,
):
    import copy
    matches = []
    for q in questions:
        if multi_turn and len(q["turns"]) != 2:
            continue
        for i in range(len(models)):
            q_id = q["question_id"]
            m = models[i]
            a = model_answers[m][q_id]

            # For magis-bench: if we have multiple turns but multi_turn=False,
            # combine all turns into a single turn for evaluation
            if ref_answers is not None and len(q["turns"]) > 1 and not multi_turn and q["category"] in MAGIS_CATS:
                ref = ref_answers["guidelines"][q_id]
                # Create copies
                copied_question = copy.deepcopy(q)
                copied_answer = copy.deepcopy(a)
                copied_ref = copy.deepcopy(ref)

                # Combine all turns into a single turn with numbered labels
                question_parts = []
                answer_parts = []
                ref_parts = []

                if 'statement' in q:
                    question_parts.append(q['statement'])

                turn_num = 0
                for idx, turn in enumerate(q["turns"]):
                    if turn.strip():  # Only include non-empty turns
                        turn_num += 1
                        question_parts.append(f"[Questão {turn_num}]\n{turn}")

                        answer_turn = a['choices'][0]['turns'][idx]
                        answer_content = answer_turn if isinstance(answer_turn, str) else answer_turn.get("content", "")
                        answer_parts.append(f"[Resposta {turn_num}]\n{answer_content}")

                        ref_turn = ref['choices'][0]['turns'][idx]
                        ref_content = ref_turn if isinstance(ref_turn, str) else ref_turn.get("content", "")
                        ref_parts.append(f"[Resposta Esperada {turn_num}]\n{ref_content}")

                combined_question = "\n\n".join(question_parts)
                combined_answer = "\n\n".join(answer_parts)
                combined_ref = "\n\n".join(ref_parts)

                # Replace turns with combined version
                copied_question["turns"] = [combined_question]
                copied_answer["choices"][0]["turns"] = [combined_answer]
                copied_ref["choices"][0]["turns"] = [combined_ref]

                # Sum up all values for the total score
                if "values" in copied_question:
                    copied_question["values"] = [sum(copied_question["values"])]

                matches.append(
                    MatchSingle(
                        copied_question,
                        m,
                        copied_answer,
                        judge,
                        ref_answer=copied_ref,
                        multi_turn=False
                    )
                )
            elif ref_answers is not None:
                ref = ref_answers["guidelines"][q_id]
                q_copy = copy.deepcopy(q)
                if 'statement' in q_copy:
                    q_copy['turns'][0] = q_copy['statement'] + ('\n' + q_copy['turns'][0]).rstrip()
                matches.append(
                    MatchSingle(
                        q_copy, m, a, judge, ref_answer=ref, multi_turn=multi_turn
                    )
                )
            else:
                matches.append(MatchSingle(dict(q), m, a, judge, multi_turn=multi_turn))
    return matches


def make_judge_pairwise(judge_model, judge_prompts):
    judges = {}
    judges["default"] = Judge(judge_model, judge_prompts["pair-v2"])
    judges["math"] = Judge(judge_model, judge_prompts["pair-math-v1"], ref_based=True)
    judges["default-mt"] = Judge(
        judge_model, judge_prompts["pair-v2-multi-turn"], multi_turn=True
    )
    judges["math-mt"] = Judge(
        judge_model,
        judge_prompts["pair-math-v1-multi-turn"],
        ref_based=True,
        multi_turn=True,
    )
    judges["magis"] = Judge(judge_model, judge_prompts.get("single-magis-v1", {}), ref_based=True)
    return judges


def make_judge_single(judge_model, judge_prompts):
    judges = {}
    judges["default"] = Judge(judge_model, judge_prompts["single-v1"])
    judges["math"] = Judge(judge_model, judge_prompts["single-math-v1"], ref_based=True)
    judges["default-mt"] = Judge(
        judge_model, judge_prompts["single-v1-multi-turn"], multi_turn=True
    )
    judges["math-mt"] = Judge(
        judge_model,
        judge_prompts["single-math-v1-multi-turn"],
        ref_based=True,
        multi_turn=True,
    )
    judges["magis"] = Judge(judge_model, judge_prompts.get("single-magis-v1", {}), ref_based=True)
    judges["magis-structured"] = Judge(judge_model, judge_prompts.get("single-magis-v2", {}), ref_based=True)
    return judges


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bench-name",
        type=str,
        default="magis_bench",
        help="The name of the benchmark question set.",
    )
    parser.add_argument(
        "--judge-file",
        type=str,
        default="data/judge_prompts.jsonl",
        help="The file of judge prompts.",
    )
    parser.add_argument("--judge-model", type=str, default="anthropic/claude-opus-4-6")
    parser.add_argument("--baseline-model", type=str, default="gpt-3.5-turbo")
    parser.add_argument(
        "--mode",
        type=str,
        default="single",
        choices=["pairwise-baseline", "pairwise-all", "single"],
        help=(
            "Evaluation mode. "
            "`pairwise-baseline` runs pairwise comparision against a baseline. "
            "`pairwise-all` runs pairwise comparision between all pairs. "
            "`single` runs single answer grading."
        ),
    )
    parser.add_argument(
        "--model-list",
        type=str,
        nargs="+",
        default=None,
        help="A list of models to be evaluated",
    )
    parser.add_argument(
        "--parallel", type=int, default=1, help="The number of concurrent API calls."
    )
    parser.add_argument(
        "--first-n", type=int, help="A debug option. Only run the first `n` judgments."
    )
    parser.add_argument("--api-base", type=str, default="https://openrouter.ai/api/v1")
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument(
        "--structured", action="store_true",
        help="Use structured output (Pydantic) for magis judgments.",
    )
    parser.add_argument(
        "--reasoning-effort",
        type=str,
        default="high",
        help="Reasoning effort for the judge model (default: 'high').",
    )
    args = parser.parse_args()

    import os
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY", "")
    openai_client = OpenAI(api_key=api_key, base_url=args.api_base)

    question_file = f"data/{args.bench_name}/question.jsonl"
    answer_dir = f"data/{args.bench_name}/model_answer"
    ref_answer_dir = f"data/{args.bench_name}/reference_answer"

    # Load questions
    questions = load_questions(question_file, None, None)

    # Load answers
    model_answers = load_model_answers(answer_dir)
    ref_answers = load_model_answers(ref_answer_dir)

    # Load judge
    judge_prompts = load_judge_prompts(args.judge_file)

    if args.first_n:
        questions = questions[: args.first_n]

    if args.model_list is None:
        models = get_model_list(answer_dir)
    else:
        models = args.model_list

    if args.mode == "single":
        judges = make_judge_single(args.judge_model, judge_prompts)
        play_a_match_func = play_a_match_single
        output_file = (
            f"data/{args.bench_name}/model_judgment/{args.judge_model.replace('/', '_')}_single.jsonl"
        )
        make_match_func = make_match_single
        baseline_model = None
    else:
        judges = make_judge_pairwise(args.judge_model, judge_prompts)
        play_a_match_func = play_a_match_pair
        output_file = (
            f"data/{args.bench_name}/model_judgment/{args.judge_model.replace('/', '_')}_pair.jsonl"
        )
        if args.mode == "pairwise-all":
            make_match_func = make_match_all_pairs
            baseline_model = None
        else:
            make_match_func = make_match
            baseline_model = args.baseline_model

    check_data(questions, model_answers, ref_answers, models, judges)

    question_math = [q for q in questions if q["category"] in NEED_REF_CATS and q["category"] not in MAGIS_CATS]
    question_default = [q for q in questions if q["category"] not in NEED_REF_CATS and q["category"] not in MAGIS_CATS]
    question_magis = [q for q in questions if q["category"] in MAGIS_CATS]

    # Make matches
    matches = []
    matches += make_match_func(
        question_default, models, model_answers, judges["default"], baseline_model
    )
    matches += make_match_func(
        question_math,
        models,
        model_answers,
        judges["math"],
        baseline_model,
        ref_answers,
    )
    matches += make_match_func(
        question_default,
        models,
        model_answers,
        judges["default-mt"],
        baseline_model,
        multi_turn=True,
    )
    matches += make_match_func(
        question_math,
        models,
        model_answers,
        judges["math-mt"],
        baseline_model,
        ref_answers,
        multi_turn=True,
    )
    magis_judge_key = "magis-structured" if args.structured else "magis"
    matches += make_match_func(
        question_magis,
        models,
        model_answers,
        judges[magis_judge_key],
        baseline_model,
        ref_answers,
    )

    match_stat = {}
    match_stat["bench_name"] = args.bench_name
    match_stat["mode"] = args.mode
    match_stat["judge"] = args.judge_model
    match_stat["baseline"] = baseline_model
    match_stat["model_list"] = models
    match_stat["total_num_questions"] = len(questions)
    match_stat["total_num_matches"] = len(matches)
    match_stat["output_path"] = output_file

    # Show match stats and prompt enter to continue
    print("Stats:")
    print(json.dumps(match_stat, indent=4))

    # Play matches
    if args.parallel == 1:
        for match in tqdm(matches):
            play_a_match_func(match, output_file=output_file, client=openai_client)
    else:

        def play_a_match_wrapper(match):
            play_a_match_func(match, output_file=output_file, client=openai_client)

        np.random.seed(0)
        np.random.shuffle(matches)

        with ThreadPoolExecutor(args.parallel) as executor:
            for match in tqdm(
                executor.map(play_a_match_wrapper, matches), total=len(matches)
            ):
                pass
