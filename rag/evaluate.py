"""Report retrieval quality on the project's Vietnamese question set."""

import argparse
import json

try:
    from rag import retrieval as r
except ModuleNotFoundError:
    import retrieval as r


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float)
    args = parser.parse_args()
    questions = json.loads((r.DATA / "evaluation_questions.json").read_text(encoding="utf-8"))
    index = r.load_index()
    model = r.load_model()
    results = []
    for q in questions:
        hits = r.search(q["question_vi"], top_k=args.top_k, min_score=args.min_score, model=model, index=index)
        rank = next((i + 1 for i, h in enumerate(hits)
                     if h["source_id"] == q["source_id"] and h["section"] == q["section"]), None) if q["source_id"] else None
        results.append({"id": q["id"], "expected": q["source_id"], "rank": rank,
                        "top_source": hits[0]["source_id"] if hits else None,
                        "top_section": hits[0]["section"] if hits else None,
                        "top_score": round(hits[0]["score"], 4) if hits else None,
                        "hits": len(hits)})
    positive = [x for x in results if x["expected"]]
    negative = [x for x in results if not x["expected"]]
    report = {"top_k": args.top_k, "min_score": args.min_score,
              "source_section_recall_at_k": sum(x["rank"] is not None for x in positive) / len(positive),
              "mrr_at_k": sum(1 / x["rank"] for x in positive if x["rank"]) / len(positive),
              "negative_abstention": sum(x["hits"] == 0 for x in negative) / len(negative),
              "questions": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
