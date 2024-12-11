# tests/test_fetcher.py

from scripts.data_processing.utils.fetchers import GitFetcher

def main():
    print("Testing GitFetcher...")
    fetcher = GitFetcher()
    fetcher.fetch_audit_reports()

if __name__ == "__main__":
    main()