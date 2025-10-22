# 📚 Hugging Face Papers Crawler & Paper QA Tool

Automated academic research toolkit: Crawl Hugging Face papers + Batch paper question answering

## ✨ Core Features

### 1. Paper Crawling & Processing
- 🔍 Search papers by keywords on Hugging Face
- 📄 Extract paper details (title, abstract, PDF link, etc.)
- 🌍 Abstract translation (multi-language support)
- 🤖 LLM-based automatic classification
- 📥 Batch download arXiv PDFs
- 📊 Retrieve publication year and citation counts

### 2. Batch Paper Question Answering
- 📖 Read all papers (PDFs) in a folder
- 🤖 Ask the same question to each paper using ChatGPT
- 💾 Export results to CSV (filename, question, answer)

## 🚀 Quick Start

### 1. Installation

⚠️ **Important**: If using conda/anaconda, use `python -m pip` to ensure packages install to the correct environment:

```bash
# Recommended (works with conda and virtualenv)
python -m pip install -r requirements.txt

# Or if using conda
conda install --file requirements.txt
```

### 2. Configure API Key (Required)

**Step 1**: Copy the template file
```bash
cp api/keys.example.py api/keys.py
```

**Step 2**: Edit `api/keys.py` and replace with your actual API key
```python
OPENAI_API_KEY = "sk-proj-your-actual-key-here"  # Replace this
```

**Step 3**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

⚠️ **Security Note**: The `api/keys.py` file is automatically ignored by git to protect your API key.

## 📝 Usage Examples

### Paper Crawling

```bash
# Basic crawling
python batch_crawler.py -k "llm hallucination" -n 10

# Crawl + Download PDFs
python batch_crawler.py -k "llm hallucination" -n 10 -d

# Full workflow: Crawl + Translate + Classify + Download + Metadata
python batch_crawler.py -k "llm hallucination" -n 10 -t zh-cn -c -d -m
```

**Parameters**
- `-k, --keywords`: Search keywords (required)
- `-n, --n`: Number of papers (required)
- `-t, --translate`: Translation language (optional)
  - Supported: `zh-cn`, `zh-tw`, `es`, `fr`, `de`, `ja`, `ko`, `ru`, `ar`, `hi`, `pt`, `it`, `nl`, `sv`, `da`, `no`, `fi`
- `-c, --classify`: Enable LLM classification (optional)
- `-d, --download-pdfs`: Download PDFs (optional)
- `-m, --get-metadata`: Retrieve citation data (optional)

### Batch Paper QA

**Mode 1: Single Question**
```bash
# Basic usage
python batch_paper_qa.py -f pdfs/llm_hallucination -q "What are the main contributions of this paper?" -p 5

# With custom output filename
python batch_paper_qa.py -f pdfs/transformer -q "Summarize the core ideas" -p 5 -o my_results.csv
```

**Mode 2: Multiple Questions from File**
```bash
# 1. Create/edit questions.txt file, one question per line:
#    What are the main contributions?
#    What datasets were used?
#    What research methodology is used?

# 2. Run with multiple questions
python batch_paper_qa.py -f pdfs/llm_hallucination -qf questions.txt -p 5
```

**Parameters**
- `-f, --folder`: PDF folder path (required)
- `-q, --question`: Single question (Mode 1, mutually exclusive with `-qf`)
- `-qf, --questions-file`: Questions file path, one per line (Mode 2, mutually exclusive with `-q`)
- `-p, --pages`: Pages to read per PDF (default: 5)
- `-o, --output`: Custom output filename (optional)
- `-d, --delay`: Delay between API calls in seconds (default: 2.0)
- `-k, --api-key`: OpenAI API key (optional, if not in `api/keys.py`)

## 📊 Output

### Paper Crawling
- **CSV**: `outputs/papers_keywords.csv`
- **PDFs**: `pdfs/keywords/`

### Paper QA
- **CSV**: `outputs/paper_qa_{folder_name}_{timestamp}.csv`
  - Example: `paper_qa_llm_hallucination_benchmark_20251021_201240.csv`
- **Single Question Mode**: 
  - Columns: `pdf_filename`, `question_1`, `answer_1`
- **Multiple Questions Mode**: 
  - Columns: `pdf_filename`, `question_1`, `answer_1`, `question_2`, `answer_2`, ...
  - Each question-answer pair gets its own column set

## 💡 Common Use Cases

```bash
# Use case 1: Collect papers on a topic and download PDFs
python batch_crawler.py -k "transformer attention" -n 20 -d

# Use case 2: Batch extract paper contributions
python batch_paper_qa.py -f pdfs/llm_hallucination_benchmark -q "What are the main contributions?" -p 5

# Use case 3: Batch extract research methods
python batch_paper_qa.py -f pdfs/llm_hallucination_benchmark -q "What research methodology is used?" -p 10

# Use case 4: Batch extract dataset information
python batch_paper_qa.py -f pdfs/llm_hallucination_benchmark -q "What datasets are used?" -p 8

# Use case 5: Comprehensive paper analysis with multiple questions
python batch_paper_qa.py -f pdfs/llm_hallucination_benchmark -qf questions.txt -p 10
```

## 🛠️ Troubleshooting

### API Key Issues
If you see "OpenAI API key not found":
1. Make sure `api/keys.py` exists (copy from `api/keys.example.py`)
2. Verify your API key is correct in `api/keys.py`
3. Alternative: Set environment variable `export OPENAI_API_KEY="sk-proj-your-key"`

### PDF Library Issues
If you see "PDF library not found":
```bash
# Use python -m pip (especially with conda)
python -m pip install pypdf

# Or install PyPDF2
python -m pip install PyPDF2
```

**Note**: Direct `pip install` may install to wrong Python environment if using conda!

### Other Common Issues
- **Rate limiting**: Increase delay with `-d 5.0` parameter
- **PDF extraction fails**: Some PDFs may be scanned images (no extractable text)
- **Memory issues**: Reduce pages to read with `-p 3` parameter

## 📁 Project Structure

```
huggingface_papers_crawler/
├── batch_crawler.py         # Paper crawling main program
├── batch_paper_qa.py        # Paper QA main program
├── questions_example.txt    # Example questions file for batch QA
├── api/                     # API configuration (🔒 keys.py in .gitignore)
│   ├── keys.example.py      # Template for API keys
│   ├── keys.py              # Your actual API keys (create from example)
│   └── README.md            # API configuration guide
├── src/                     # Core modules
│   ├── crawler.py           # Paper URL extraction
│   ├── paper_detail_crawler.py  # Paper detail scraping
│   ├── advanced_processor.py    # Translation & classification
│   └── paper_metadata_api.py    # Citation & metadata retrieval
├── prompts/                 # Prompt templates for LLM
│   ├── classification_template.py
│   └── reading_template.py
├── pdfs/                    # Downloaded PDF files (organized by keywords)
└── outputs/                 # Generated CSV files
```

## 🔐 Security

- ✅ API keys are stored in `api/keys.py` which is automatically ignored by git
- ✅ Never commit `api/keys.py` to version control
- ✅ Use `api/keys.example.py` as a template for team collaboration
- ✅ Multiple key sources supported: file > environment variable > parameter

---

**Tech Stack**: Python · BeautifulSoup · Pandas · OpenAI · PyPDF2

**License**: MIT

**Contributing**: Pull requests are welcome! Please ensure your code follows the existing style.
