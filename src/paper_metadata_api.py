import os
import requests
import time
import logging
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperMetadataAPI:
    def __init__(self):
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.crossref_base = "https://api.crossref.org"
        self.openalex_base = "https://api.openalex.org/works"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PaperMetadataAPI"})
        self.crossref_mailto = os.getenv("CROSSREF_MAILTO", "your-email@example.com")
        self.s2_api_key = os.getenv("S2_API_KEY", None)

    def get_paper_metadata_google_scholar(self, title: str, max_retries: int = 3) -> Optional[Dict]:
        return None

    def get_paper_metadata_semantic_scholar(self, title: str) -> Optional[Dict]:
        try:
            url = f"{self.semantic_scholar_base}/paper/search"
            params = {"query": title, "limit": 1, "fields": "year,citationCount"}
            headers = {}
            if self.s2_api_key:
                headers["x-api-key"] = self.s2_api_key
            r = self.session.get(url, params=params, headers=headers, timeout=10)
            if r.status_code == 429:
                logger.warning("Semantic Scholar rate limited.")
                return None
            r.raise_for_status()
            data = r.json().get("data", [])
            if not data:
                return None
            p = data[0]
            return {
                "year": p.get("year"),
                "citation_count": p.get("citationCount", 0),
                "source": "semantic_scholar"
            }
        except Exception as e:
            logger.warning(f"S2 failed: {e}")
            return None

    def get_paper_metadata_crossref(self, title: str) -> Optional[Dict]:
        try:
            url = f"{self.crossref_base}/works"
            params = {"query.title": title, "rows": 1, "mailto": self.crossref_mailto}
            r = self.session.get(url, params=params, timeout=10)
            r.raise_for_status()
            items = r.json().get("message", {}).get("items", [])
            if not items:
                return None
            w = items[0]
            year = None
            for key in ("published-print", "published-online", "issued"):
                obj = w.get(key, {})
                parts = obj.get("date-parts", [])
                if parts and parts[0] and parts[0][0]:
                    year = parts[0][0]
                    break
            return {"year": year, "citation_count": 0, "source": "crossref"}
        except Exception as e:
            logger.warning(f"Crossref failed: {e}")
            return None

    def get_paper_metadata_openalex(self, title: str) -> Optional[Dict]:
        try:
            url = self.openalex_base
            params = {"filter": f"display_name.search:{title}", "per-page": 1}
            r = self.session.get(url, params=params, timeout=10)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            w = results[0]
            return {
                "year": w.get("publication_year"),
                "citation_count": w.get("cited_by_count", 0),
                "source": "openalex"
            }
        except Exception as e:
            logger.warning(f"OpenAlex failed: {e}")
            return None

    def get_paper_metadata(self, title: str, prefer_google_scholar: bool = True) -> Optional[Dict]:
        if prefer_google_scholar:
            m = self.get_paper_metadata_google_scholar(title)
            if m: return m
        time.sleep(0.2)
        m = self.get_paper_metadata_semantic_scholar(title)
        if m: return m
        time.sleep(0.2)
        m = self.get_paper_metadata_crossref(title)
        if m: return m
        time.sleep(0.2)
        return self.get_paper_metadata_openalex(title)

    def batch_get_metadata(self, titles: List[str], delay: float = 2.0) -> List[Dict]:
        results = []
        for i, t in enumerate(titles):
            logger.info(f"{i+1}/{len(titles)}: {t[:60]}...")
            m = self.get_paper_metadata(t)
            results.append(m or {"year": None, "citation_count": 0, "source": "not_found"})
            if i < len(titles) - 1:
                time.sleep(delay)
        return results

def main():
    api = PaperMetadataAPI()
    titles = [
        "Attention Is All You Need",
        "Differential Transformer"
    ]
    print(api.batch_get_metadata(titles))

if __name__ == "__main__":
    main()
