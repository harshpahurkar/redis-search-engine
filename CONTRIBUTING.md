# Contributing

Thank you for considering contributing!

## Development Setup

1. Clone the repo
2. `pip install -r requirements.txt`
3. Start Redis: `redis-server` or `docker run -d -p 6379:6379 redis`
4. Run the indexer: `python src/indexer.py`
5. Run search: `python src/search.py`

## Code Style

- Follow PEP 8 conventions
- Write docstrings for public functions
