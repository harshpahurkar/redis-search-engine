import argparse
import json
from pathlib import Path

from search_engine import SearchEngine


def cmd_index(args: argparse.Namespace) -> None:
    engine = SearchEngine(redis_url=args.redis, prefix=args.prefix)
    if args.clear:
        engine.clear()
    engine.load_json(args.json)
    print(f"Indexed: {args.json}")


def cmd_search(args: argparse.Namespace) -> None:
    engine = SearchEngine(redis_url=args.redis, prefix=args.prefix)
    hits = engine.search(args.query, offset=args.offset, limit=args.limit)
    if args.json_output:
        print(json.dumps([hit.__dict__ for hit in hits], indent=2))
        return

    print(f"Query: {args.query}")
    for hit in hits:
        title = hit.title or "(untitled)"
        print(f"- {hit.doc_id} | {title} | score={hit.score:.3f}")


def cmd_remove(args: argparse.Namespace) -> None:
    engine = SearchEngine(redis_url=args.redis, prefix=args.prefix)
    engine.remove_document(args.doc_id)
    print(f"Removed: {args.doc_id}")


def cmd_stats(args: argparse.Namespace) -> None:
    engine = SearchEngine(redis_url=args.redis, prefix=args.prefix)
    doc_count = engine.redis.scard(engine._key("docs"))
    term_count = sum(1 for _ in engine.redis.scan_iter(match=engine._key("term", "*")))
    print(f"docs={doc_count} terms={term_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Redis TF-IDF search engine")
    parser.add_argument("--redis", default="redis://localhost:6379/0")
    parser.add_argument("--prefix", default="se")

    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Index documents from JSON")
    p_index.add_argument("--json", default=str(Path(__file__).resolve().parents[1] / "data" / "sample_docs.json"))
    p_index.add_argument("--clear", action="store_true")
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="Search for documents")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--offset", type=int, default=0)
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--json-output", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_remove = sub.add_parser("remove", help="Remove a document")
    p_remove.add_argument("doc_id")
    p_remove.set_defaults(func=cmd_remove)

    p_stats = sub.add_parser("stats", help="Show index stats")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
