# eval/run_eval.py
import time
import statistics
import yaml
from src.llm_engine import LLMEngine
from src.filter import filter_issues, load_config

def evaluate_agent():
    with open("eval/cases.yaml", "r") as f:
        cases = yaml.safe_load(f)

    cfg = load_config(".ai-review.yml")
    engine = LLMEngine()

    tp, fp, fn, tn = 0, 0, 0, 0
    latencies = []
    scores_by_case = []

    for case in cases:
        with open(case["file"], "r") as cf:
            content = cf.read()

        # 3 exécutions pour mesurer la stabilité/reproductibilité
        run_scores = []
        for _ in range(3):
            t0 = time.time()
            res = engine.analyze_patch(case["file"], content)
            latencies.append(time.time() - t0)
            run_scores.append(res.score)

        scores_by_case.append(statistics.stdev(run_scores) if len(run_scores) > 1 else 0.0)

        # Application du filtre
        filtered_issues = filter_issues(res.issues, cfg)
        has_expected = len(case["expected"]) > 0
        has_found = len(filtered_issues) > 0

        if has_expected and has_found:
            tp += 1
        elif not has_expected and has_found:
            fp += 1
        elif has_expected and not has_found:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    print(f"Précision: {precision:.2f} | Rappel: {recall:.2f} | F1: {f1:.2f} | FPR: {fpr:.2f}")
    print(f"Temps moyen: {statistics.mean(latencies):.2f}s | Écart-type moyen des notes: {statistics.mean(scores_by_case):.2f}")

if __name__ == "__main__":
    evaluate_agent()