import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import time
import csv
import os


class PaperDetailCrawler:
    """
    Crawler to extract detailed information from individual paper pages
    """
    
    def __init__(self):
        """Initialize the paper detail crawler"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_paper_detail(self, paper_url: str) -> Dict:
        """
        Crawl detailed information from a single paper page
        
        Args:
            paper_url: URL of the paper page
            
        Returns:
            Dictionary containing paper details
        """
        try:
            response = self.session.get(paper_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract paper information
            paper_info = {
                'url': paper_url,
                'title': self._extract_title(soup),
                'llm_summary': self._extract_llm_summary(soup),
                'abstract': self._extract_abstract(soup),
                'pdf_url': self._extract_pdf_url(soup),
                'arxiv_id': self._extract_arxiv_id(paper_url)
            }
            
            return paper_info
            
        except requests.RequestException as e:
            print(f"Error crawling paper {paper_url}: {e}")
            return {'url': paper_url, 'error': str(e)}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract paper title"""
        # Try different selectors for title
        title_selectors = [
            'h1[data-testid="paper-title"]',
            'h1.title',
            'h1',
            '.paper-title',
            '[data-testid="paper-title"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return ""
    
    def _extract_llm_summary(self, soup: BeautifulSoup) -> str:
        """Extract LLM Summary"""
        # Look for the specific class for LLM summary
        summary_elem = soup.select_one('p.text-blue-700.dark\\:text-blue-400')
        if summary_elem:
            return summary_elem.get_text(strip=True)
        return ""
    
    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """Extract paper abstract"""
        # Look for the specific class for abstract
        abstract_elem = soup.select_one('p.text-gray-600')
        if abstract_elem:
            return abstract_elem.get_text(strip=True)
        return ""
    
    
    def _extract_pdf_url(self, soup: BeautifulSoup) -> str:
        """Extract PDF download URL"""
        # Look for the specific class for PDF button
        pdf_elem = soup.select_one('a.btn.inline-flex.h-9.items-center')
        if pdf_elem and pdf_elem.get('href'):
            href = pdf_elem['href']
            if href.startswith('http'):
                return href
            else:
                return f"https://huggingface.co{href}"
        
        return ""
    
    def _extract_arxiv_id(self, paper_url: str) -> str:
        """Extract arXiv ID from paper URL"""
        # Extract arXiv ID from URL like /papers/2504.17550
        import re
        match = re.search(r'/papers/(\d+\.\d+)', paper_url)
        if match:
            return match.group(1)
        return ""
    
    def crawl_multiple_papers(self, paper_urls: list, delay: float = 1.0) -> list:
        """
        Crawl multiple paper details with rate limiting
        
        Args:
            paper_urls: List of paper URLs
            delay: Delay between requests in seconds
            
        Returns:
            List of paper detail dictionaries
        """
        results = []
        
        for i, url in enumerate(paper_urls, 1):
            print(f"Crawling paper {i}/{len(paper_urls)}: {url}")
            
            paper_detail = self.crawl_paper_detail(url)
            results.append(paper_detail)
            
            # Rate limiting
            if i < len(paper_urls):
                time.sleep(delay)
        
        return results
    
    def export_to_csv(self, paper_details: List[Dict], filename: str = "papers.csv") -> str:
        """
        Export paper details to CSV file
        
        Args:
            paper_details: List of paper detail dictionaries
            filename: Output CSV filename
            
        Returns:
            Path to the created CSV file
        """
        if not paper_details:
            print("No paper details to export.")
            return ""
        
        # Get the directory of the current script and navigate to outputs folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_dir = os.path.join(current_dir, '..', 'outputs')
        
        # Create outputs directory if it doesn't exist
        os.makedirs(outputs_dir, exist_ok=True)
        
        csv_path = os.path.join(outputs_dir, filename)
        
        # Create CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['title', 'llm_summary', 'abstract', 'pdf_url', 'arxiv_id', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for paper in paper_details:
                # Only include valid papers (no errors)
                if 'error' not in paper:
                    row = {
                        'title': paper.get('title', ''),
                        'llm_summary': paper.get('llm_summary', ''),
                        'abstract': paper.get('abstract', ''),
                        'pdf_url': paper.get('pdf_url', ''),
                        'arxiv_id': paper.get('arxiv_id', ''),
                        'url': paper.get('url', '')
                    }
                    writer.writerow(row)
        
        print(f"CSV file exported to: {csv_path}")
        return csv_path
