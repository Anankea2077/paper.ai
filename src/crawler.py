import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
import os
import time


class PaperCrawler:
    def __init__(self, keywords: List[str], N: int = 10):
        """
        Initialize crawler with keywords list
        
        Args:
            keywords: List of keywords (e.g., ["llm", "Hallucination"])
            N: Number of papers to crawl (default: 10)
        """
        self.keywords = keywords
        self.keyword_combination = '+'.join(keywords)  # Join keywords with '+'
        self.N = N  # Number of papers to crawl
        self.base_url = "https://huggingface.co/papers/trending"
        self.paper_urls = []  # Store extracted paper URLs
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _build_url(self) -> str:
        """Build search URL for keyword combination"""
        encoded_keywords = urllib.parse.quote_plus(self.keyword_combination)
        return f"{self.base_url}?q={encoded_keywords}"
    
    def extract_paper_urls(self) -> List[str]:
        """
        Extract paper URLs from the page (limited to N papers)
        
        Returns:
            List of paper URLs (max N papers)
        """
        url = self._build_url()
        paper_urls = []
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all paper blocks with the specific structure
            paper_blocks = soup.find_all('div', class_='flex w-full gap-6')
            
            for block in paper_blocks:
                if len(paper_urls) >= self.N:
                    break
                    
                # Find the h3 element containing the paper link
                h3_elem = block.find('h3', class_='mb-3 text-lg/6 font-semibold hover:underline peer-hover:underline 2xl:text-[1.2rem]/6')
                if h3_elem:
                    link_elem = h3_elem.find('a', class_='line-clamp-3 cursor-pointer text-balance')
                    if link_elem and link_elem.get('href'):
                        paper_url = f"https://huggingface.co{link_elem['href']}"
                        paper_urls.append(paper_url)
                        
        except requests.RequestException as e:
            print(f"Error extracting URLs: {e}")
            
        return paper_urls

    def crawl_papers(self) -> List[Dict]:
        """
        Crawl papers for the keyword combination (limited to N papers)
        
        Returns:
            List of paper dictionaries (max N papers)
        """
        url = self._build_url()
        papers = []
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all paper blocks
            paper_blocks = soup.find_all('div', class_='flex w-full gap-6')
            
            for block in paper_blocks:
                if len(papers) >= self.N:
                    break
                    
                paper = self._extract_paper_info(block)
                if paper:
                    papers.append(paper)
                    
        except requests.RequestException as e:
            print(f"Error crawling papers: {e}")
            
        return papers
    
    def _extract_paper_info(self, element) -> Dict:
        """Extract paper URL from HTML element"""
        # Find the h3 element with the paper link
        h3_elem = element.find('h3', class_='mb-3 text-lg/6 font-semibold hover:underline peer-hover:underline 2xl:text-[1.2rem]/6')
        if not h3_elem:
            return None
            
        # Extract link from the h3 element
        link_elem = h3_elem.find('a', class_='line-clamp-3 cursor-pointer text-balance')
        if not link_elem:
            return None
            
        paper_url = f"https://huggingface.co{link_elem['href']}"
        
        return {
            'url': paper_url
        }
    
    def generate_url(self) -> str:
        """
        Generate the search URL for the keyword combination
        
        Returns:
            The complete search URL
        """
        url = self._build_url()
        print(f"Generated URL for keywords {self.keywords}: {url}")
        return url
    
    def download_pdf(self, pdf_url: str, filename: str, delay: float = 2.0) -> str:
        """
        Download PDF from URL and save to pdfs folder
        
        Args:
            pdf_url: URL of the PDF to download
            filename: Filename to save the PDF as
            delay: Delay between downloads to avoid rate limiting
            
        Returns:
            Path to the downloaded PDF file, or None if failed
        """
        try:
            # Check if it's an arXiv URL
            if not self._is_arxiv_url(pdf_url):
                print(f"⚠️  Skipping non-arXiv URL: {pdf_url}")
                return None
            
            # Convert to PDF URL if needed
            actual_pdf_url = self._convert_to_pdf_url(pdf_url)
            print(f"📄 Converting URL: {pdf_url} -> {actual_pdf_url}")
            
            # Create pdfs directory structure
            keywords_folder = '_'.join(self.keywords).replace(' ', '_')
            pdfs_dir = os.path.join('pdfs', keywords_folder)
            os.makedirs(pdfs_dir, exist_ok=True)
            
            # Full path for the PDF file
            pdf_path = os.path.join(pdfs_dir, filename)
            
            # Skip if file already exists
            if os.path.exists(pdf_path):
                print(f"📄 PDF already exists: {pdf_path}")
                return pdf_path
            
            print(f"⬇️  Downloading PDF: {actual_pdf_url}")
            
            # Download the PDF
            response = self.session.get(actual_pdf_url, stream=True)
            response.raise_for_status()
            
            # Save the PDF
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ PDF downloaded: {pdf_path}")
            
            # Add delay to avoid rate limiting
            if delay > 0:
                time.sleep(delay)
            
            return pdf_path
            
        except Exception as e:
            print(f"❌ Error downloading PDF {pdf_url}: {e}")
            return None
    
    def _is_arxiv_url(self, url: str) -> bool:
        """
        Check if URL is an arXiv URL (either /abs/ or /pdf/)
        
        Args:
            url: URL to check
            
        Returns:
            True if it's an arXiv URL, False otherwise
        """
        if not isinstance(url, str):
            return False
        if not url:
            return False
        return 'arxiv.org' in url and ('/abs/' in url or '/pdf/' in url)
    
    def _convert_to_pdf_url(self, url: str) -> str:
        """
        Convert arXiv /abs/ URL to /pdf/ URL
        
        Args:
            url: arXiv URL (either /abs/ or /pdf/)
            
        Returns:
            PDF URL
        """
        if not isinstance(url, str) or not url or 'arxiv.org' not in url:
            return url
        
        if '/abs/' in url:
            # Convert /abs/ to /pdf/ and add .pdf extension
            return url.replace('/abs/', '/pdf/') + '.pdf'
        elif '/pdf/' in url and not url.endswith('.pdf'):
            # Add .pdf extension if missing
            return url + '.pdf'
        
        return url
    
    def download_pdfs_from_papers(self, papers: List[Dict], delay: float = 2.0) -> List[Dict]:
        """
        Download PDFs for all papers that have arXiv URLs
        
        Args:
            papers: List of paper dictionaries containing pdf_url
            delay: Delay between downloads
            
        Returns:
            List of papers with added 'pdf_path' field
        """
        downloaded_papers = []
        
        for i, paper in enumerate(papers, 1):
            paper_copy = paper.copy()
            
            pdf_url = paper.get('pdf_url', '')
            if pdf_url and self._is_arxiv_url(pdf_url):
                # Extract filename from URL or create one
                filename = self._extract_filename_from_url(pdf_url, paper.get('title', ''))
                
                print(f"\n[{i}/{len(papers)}] Processing: {paper.get('title', 'Unknown')[:50]}...")
                pdf_path = self.download_pdf(pdf_url, filename, delay)
                paper_copy['pdf_path'] = pdf_path
            else:
                paper_copy['pdf_path'] = None
                print(f"\n[{i}/{len(papers)}] No arXiv PDF available for: {paper.get('title', 'Unknown')[:50]}...")
            
            downloaded_papers.append(paper_copy)
        
        return downloaded_papers
    
    def _extract_filename_from_url(self, pdf_url: str, title: str = '') -> str:
        """
        Extract or generate filename for PDF
        
        Args:
            pdf_url: URL of the PDF
            title: Paper title for fallback filename
            
        Returns:
            Safe filename for the PDF
        """
        try:
            # Try to extract arXiv ID from URL
            if '/pdf/' in pdf_url:
                arxiv_id = pdf_url.split('/pdf/')[-1].replace('.pdf', '')
                return f"{arxiv_id}.pdf"
        except:
            pass
        
        # Fallback: create filename from title
        if isinstance(title, str) and title:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            return f"{safe_title}.pdf"
        
        # Final fallback
        return "paper.pdf"
