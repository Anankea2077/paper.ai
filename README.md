# Hugging Face Paper Ranking Crawler

Hugging Face paper ranking (formerly Papers with Code) crawler for automated paper research, integrated with LLM automatic classification and other advanced features.

## Technology Stack

- **Python 3.x**
- **requests**: HTTP requests
- **BeautifulSoup4**: HTML parsing
- **pandas**: Data manipulation
- **openai**: OpenAI API integration (for classification)

## Features

- **Keyword Search**: Input keywords to search papers on Hugging Face
- **Paper Extraction**: Extract paper URLs from search results
- **Detail Crawling**: Get detailed information from each paper page
- **CSV Export**: Export results to CSV files in `outputs/` folder
- **Abstract Translation**: Translate abstracts to specified languages (e.g., Chinese)
- **Paper Classification**: Classify papers using OpenAI API
- **PDF Download**: Download arXiv PDFs to organized folders

### Extracted Information
- Title
- LLM Summary (AI-generated summary)
- Abstract (original paper abstract)
- PDF URL
- ArXiv ID
- PDF Path (local path when downloaded)
- Source URL
- Abstract Translation (new column)
- Category (new column)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key (for classification features)
```bash
# Edit src/advanced_processor.py directly
# Open src/advanced_processor.py and paste your API key in the OPENAI_API_KEY constant at the top
```

Get your API key from: https://platform.openai.com/api-keys

## Quick Start

### Command Line Usage

```bash
# Crawl papers + Download PDFs
python test_complete_workflow.py --keywords "llm hallucination" --n 5 --download-pdfs

# Full workflow: Crawl + Translate + Classify + Download PDFs
python test_complete_workflow.py --keywords "llm hallucination" --n 5 --translate zh-cn --classify --download-pdfs
```

### Parameters
- `--keywords, -k`: Search keywords (required)
- `--n, -n`: Number of papers to crawl (required)
- `--translate, -t`: Target language for translation (optional)
- `--classify, -c`: Enable LLM classification (optional)
- `--download-pdfs, -d`: Download arXiv PDFs to pdfs/keywords folder (optional)

### Supported Languages
`zh-cn`, `zh-tw`, `es`, `fr`, `de`, `ja`, `ko`, `ru`, `ar`, `hi`, `pt`, `it`, `nl`, `sv`, `da`, `no`, `fi`

### Output
- **CSV File**: `outputs/papers_keywords.csv` (contains all paper data, filename based on search keywords)
- **PDF Files**: `pdfs/keywords/` (organized by search keywords when `--download-pdfs` is used)

## Advanced Features

### Unsupervised Paper Classification

The classification feature uses an unsupervised approach where the LLM analyzes all papers together:

- **Input**: All papers' titles and summaries are sent to the LLM in a single batch
- **Process**: LLM identifies natural themes and creates meaningful categories based on the actual content
- **Output**: JSON response containing both category definitions and individual paper classifications
- **Advantage**: Categories emerge naturally from the data rather than being predefined

Example classification output:
```
Created 4 categories:
- Hallucination Benchmarking: Research focused on developing benchmarks...
- Contextual Tagging for Hallucination Mitigation: Research centered around using context...
- Generalization and Training Thresholds: Exploration of hallucination causes...
- Ethical Implications of Hallucinations in LLMs: Investigation into ethical considerations...
```

### PDF Download Feature

The PDF download feature automatically downloads arXiv papers to organized folders:

- **Automatic Detection**: Only downloads papers with valid arXiv URLs
- **URL Conversion**: Converts `/abs/` URLs to `/pdf/` URLs automatically  
- **Organized Storage**: Creates `pdfs/keywords/` folder structure based on search terms
- **Smart Naming**: Uses arXiv ID or paper title for filename generation
- **Duplicate Prevention**: Skips downloading if PDF already exists

Example folder structure:
```
pdfs/
└── llm_hallucination/
    ├── 2504.17550.pdf
    ├── 2306.06085.pdf
    └── ...
```
