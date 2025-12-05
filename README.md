# Redis Search Engine

A TF-IDF search engine built on **Redis sorted sets** — index documents, search with relevance ranking, and manage your index through a clean CLI.

---

## Features

- **TF-IDF Scoring** — Ranks results by term frequency x inverse document frequency at query time
- **Tokenization & Stop Words** — Cleans input text and filters common English stop words for better relevance
- **Negative Terms** — Exclude documents containing specific words (e.g., `search -redis`)
- **JSON Bulk Loader** — Index documents from JSON files in a single command
- **Redis Pipelines** — Batch operations for efficient indexing and removal
- **CLI Interface** — `index`, `search`, `remove`, `stats` commands with JSON output support

## How It Works

```
Document Text
     |
     v
+-----------+     +-------------+     +----------------------------+
| Tokenize  |---->| Stop Word   |---->|  Count Term Frequencies    |
| (lowercase,     |  Filter     |     |  per Document              |
|  clean)   |     +-------------+     +-------------+--------------+
+-----------+                                       |
                                                    v
                                     +----------------------------+
                                     |  Store in Redis:            |
                                     |  term -> sorted set of      |
                                     |  {doc_id: tf_score}         |
                                     |  doc  -> hash {text, title} |
                                     +----------------------------+

Search Query
     |
     v
+-----------+     +--------------+     +----------------------------+
| Tokenize  |---->| Compute IDF  |---->|  ZUNIONSTORE with IDF      |
|           |     | weights      |     |  weights -> ranked results  |
+-----------+     +--------------+     +----------------------------+
```

## Project Structure

```
redis-search-engine/
├── src/
│   ├── search_engine.py    # Core SearchEngine class (tokenizer, indexer, TF-IDF scorer)
│   ├── cli.py              # argparse CLI with index/search/remove/stats commands
│   └── demo.py             # Quick demo script
├── data/
│   └── sample_docs.json    # Sample documents for testing
├── requirements.txt
├── LICENSE
└── README.md
```

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Data Store | Redis (sorted sets, hashes, sets) |
| Algorithm | TF-IDF (term frequency-inverse document frequency) |
| CLI | argparse |
| Client | redis-py 5.0+ |

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Redis** running locally (default: `localhost:6379`)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure Redis is running
redis-cli ping   # Should return PONG
```

### Index & Search

```bash
# Index the sample documents (clears existing index first)
python src/cli.py index --clear

# Search for documents
python src/cli.py search --query "redis search"
```

Output:
```
Query: redis search
- doc1 | Redis basics | score=3.218
- doc3 | Python and Redis | score=2.099
- doc2 | Search with TF-IDF | score=1.693
```

### All CLI Commands

```bash
# Index documents from a custom JSON file
python src/cli.py index --json path/to/docs.json --clear

# Search with negative terms (exclude "redis" from results)
python src/cli.py search --query "search -redis"

# Get JSON output for programmatic use
python src/cli.py search --query "redis" --json-output

# Paginate results
python src/cli.py search --query "redis" --offset 0 --limit 5

# Remove a specific document
python src/cli.py remove doc2

# View index statistics
python src/cli.py stats
```

### Programmatic Usage

```python
from search_engine import SearchEngine

engine = SearchEngine(redis_url="redis://localhost:6379/0")

# Index a document
engine.index_document("doc1", "Redis is a fast in-memory store", title="Redis Intro")

# Search
hits = engine.search("redis store")
for hit in hits:
    print(f"{hit.doc_id}: {hit.title} (score={hit.score:.3f})")

# Remove
engine.remove_document("doc1")

# Clear entire index
engine.clear()
```

## JSON Document Format

```json
[
  {
    "id": "doc1",
    "title": "Redis Basics",
    "text": "Redis is an in-memory data structure store used as a database and cache."
  }
]
```

Fields: `id` (required), `text` (required), `title` (optional).

## License

MIT — see [LICENSE](LICENSE) for details.
