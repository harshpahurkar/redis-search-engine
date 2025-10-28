import argparse
from pathlib import Path

from search_engine import SearchEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Redis TF-IDF search demo")
    parser.add_argument("--redis", default="redis://localhost:6379/0")
    parser.add_argument("--prefix", default="se")
    parser.add_argument("--reindex", action="store_true", help="Rebuild the index")
    parser.add_argument("--query", default="redis search", help="Search query")
    args = parser.parse_args()

    engine = SearchEngine(redis_url=args.redis, prefix=args.prefix)
    data_path = Path(__file__).resolve().parents[1] / "data" / "sample_docs.json"

    if args.reindex:
        engine.load_json(str(data_path))

    hits = engine.search(args.query)
    print(f"Query: {args.query}")
    for hit in hits:
        title = hit.title or "(untitled)"
        print(f"- {hit.doc_id} | {title} | score={hit.score:.3f}")


if __name__ == "__main__":
    main()
