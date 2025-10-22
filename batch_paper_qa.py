#!/usr/bin/env python3
"""
Batch Paper Question Answering Tool

Features:
- Read all PDF files in a specified folder
- Extract text from first P pages of each PDF
- Use ChatGPT API to ask the same question for each PDF
- Save results to CSV file (PDF filename, question, answer)

Usage Examples:
python batch_paper_qa.py --folder pdfs/llm_hallucination --question "What are the main contributions of this paper?" --pages 5
python batch_paper_qa.py -f pdfs/llm_code_generation -q "What is the main research method?" -p 10
"""

import os
import sys
import argparse
import pandas as pd
import time
from typing import List, Dict, Optional
from openai import OpenAI

# Add src and api directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Load API keys
try:
    from keys import OPENAI_API_KEY as API_KEY_FROM_FILE
except ImportError:
    API_KEY_FROM_FILE = None
    print("⚠️  Warning: api/keys.py not found. Please create it from api/keys.example.py")

# Load prompt template
def load_reading_template():
    """Load reading template from prompts directory"""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'prompts', 'reading_template.py')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Execute template file to get the READING_TEMPLATE variable
        namespace = {}
        exec(template_content, namespace)
        return namespace.get('READING_TEMPLATE', None)
    except Exception as e:
        print(f"⚠️  Warning: Could not load reading template: {e}")
        return None

# Try to import PyPDF2
try:
    from PyPDF2 import PdfReader
    PDF_LIBRARY = "PyPDF2"
except ImportError:
    try:
        import pypdf
        from pypdf import PdfReader
        PDF_LIBRARY = "pypdf"
    except ImportError:
        print("❌ Error: PDF library not found!")
        print("Please install PyPDF2 or pypdf:")
        print("  pip install PyPDF2")
        print("  OR")
        print("  pip install pypdf")
        sys.exit(1)

class BatchPaperQuestionAnswering:
    """Batch Paper Question Answering Processor"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize batch paper QA processor
        
        Args:
            api_key: OpenAI API key (optional, will use constant or environment variable if not provided)
        """
        # Set OpenAI API Key
        self.api_key = None
        if api_key:
            self.api_key = api_key
            print(f"✅ Using API key from parameter")
        elif API_KEY_FROM_FILE and not API_KEY_FROM_FILE.startswith("sk-proj-xxxx"):
            self.api_key = API_KEY_FROM_FILE
            print(f"✅ Using API key from api/keys.py")
        elif os.getenv('OPENAI_API_KEY'):
            self.api_key = os.getenv('OPENAI_API_KEY')
            print(f"✅ Using API key from environment variable")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ OpenAI API key set successfully")
        else:
            self.client = None
            print("⚠️  Warning: OpenAI API key not found!")
            print("   1. Copy api/keys.example.py to api/keys.py and add your key")
            print("   2. Or set OPENAI_API_KEY environment variable")
            print("   3. Or pass api_key parameter")
            print("   Get your key at: https://platform.openai.com/api-keys")
        
        # Load reading template
        self.reading_template = load_reading_template()
        if self.reading_template:
            print(f"✅ Reading template loaded successfully")
        else:
            print(f"⚠️  Warning: Reading template not loaded, using fallback")
    
    def extract_pdf_text(self, pdf_path: str, max_pages: int = 5) -> str:
        """
        Extract text from PDF file (first max_pages pages)
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to read
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            pages_to_read = min(max_pages, total_pages)
            
            text_content = []
            for i in range(pages_to_read):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {i+1} ---\n{text}")
            
            full_text = "\n\n".join(text_content)
            
            print(f"  📄 Successfully extracted {pages_to_read}/{total_pages} pages, {len(full_text)} characters total")
            return full_text
            
        except Exception as e:
            print(f"  ❌ Failed to extract PDF text: {e}")
            return ""
    
    def ask_question(self, pdf_content: str, question: str, 
                    model: str = "gpt-3.5-turbo", 
                    max_tokens: int = 1000) -> str:
        """
        Use ChatGPT API to answer questions about PDF content
        
        Args:
            pdf_content: PDF text content
            question: Question to ask
            model: OpenAI model name
            max_tokens: Maximum number of tokens to return
            
        Returns:
            ChatGPT's answer
        """
        if not self.client:
            return "Error: OpenAI API key not set"
        
        try:
            # Build prompt using template
            if self.reading_template:
                # Use template from file
                prompt = self.reading_template.format(
                    pdf_content=pdf_content[:8000],  # Limit content length to avoid token limit
                    question=question
                )
            else:
                # Fallback: use hardcoded prompt
                prompt = f"""You are a professional academic paper analysis assistant. Please carefully read the following paper content and answer the user's question.

Paper Content:
{pdf_content[:8000]}

Question:
{question}

Please provide a detailed and accurate answer based on the paper content. If the paper does not contain relevant information, please state it clearly.

Provide the answer in both Chinese and English versions.
"""
            
            # Call OpenAI API (new version)
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"  ✅ ChatGPT answered successfully ({len(answer)} characters)")
            return answer
            
        except Exception as e:
            error_msg = f"API call failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            return error_msg
    
    def process_folder(self, folder_path: str, questions: List[str], 
                      max_pages: int = 5, delay: float = 2.0,
                      model: str = "gpt-3.5-turbo") -> pd.DataFrame:
        """
        Process all PDF files in a folder with one or multiple questions
        
        Args:
            folder_path: PDF folder path
            questions: List of questions to ask (can be single question or multiple)
            max_pages: Maximum number of pages to read from each PDF
            delay: Delay between API calls (seconds)
            model: OpenAI model name
            
        Returns:
            DataFrame containing results (pdf_filename, question_1, answer_1, question_2, answer_2, ...)
        """
        # Check if folder exists
        if not os.path.exists(folder_path):
            print(f"❌ Error: Folder does not exist: {folder_path}")
            return pd.DataFrame()
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"❌ Error: No PDF files found in folder: {folder_path}")
            return pd.DataFrame()
        
        print(f"\n{'='*60}")
        print(f"📚 Found {len(pdf_files)} PDF files")
        print(f"❓ Number of questions: {len(questions)}")
        for idx, q in enumerate(questions, 1):
            print(f"   Q{idx}: {q[:80]}{'...' if len(q) > 80 else ''}")
        print(f"📄 Reading first {max_pages} pages from each PDF")
        print(f"{'='*60}\n")
        
        # Process each PDF
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file}")
            
            pdf_path = os.path.join(folder_path, pdf_file)
            
            # Extract PDF text once per PDF
            pdf_content = self.extract_pdf_text(pdf_path, max_pages)
            
            if not pdf_content:
                print(f"  ⚠️  Skipped (unable to extract text)")
                # Create error result with all questions
                result = {'pdf_filename': pdf_file}
                for q_idx, question in enumerate(questions, 1):
                    result[f'question_{q_idx}'] = question
                    result[f'answer_{q_idx}'] = "Error: Unable to extract PDF text"
                results.append(result)
                continue
            
            # Ask all questions for this PDF
            result = {'pdf_filename': pdf_file}
            for q_idx, question in enumerate(questions, 1):
                print(f"  ❓ Question {q_idx}/{len(questions)}: {question[:50]}...")
                answer = self.ask_question(pdf_content, question, model=model)
                result[f'question_{q_idx}'] = question
                result[f'answer_{q_idx}'] = answer
                
                # Small delay between questions for the same PDF
                if q_idx < len(questions):
                    time.sleep(0.5)
            
            results.append(result)
            
            # Delay to avoid API rate limiting (between PDFs)
            if i < len(pdf_files):
                print(f"  ⏳ Waiting {delay} seconds before next PDF...\n")
                time.sleep(delay)
        
        # Create DataFrame
        df = pd.DataFrame(results)
        print(f"\n{'='*60}")
        print(f"✅ Processing complete! Processed {len(results)} PDF files")
        print(f"{'='*60}\n")
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_filename: str = None,
                    output_dir: str = "outputs", folder_name: str = None) -> str:
        """
        Save results to CSV file
        
        Args:
            df: Results DataFrame
            output_filename: Output filename (optional)
            output_dir: Output directory
            folder_name: Folder name to include in filename (optional)
            
        Returns:
            Path to saved file
        """
        if df.empty:
            print("❌ Error: No data to save")
            return ""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename (if not provided)
        if output_filename is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if folder_name:
                output_filename = f"paper_qa_{folder_name}_{timestamp}.csv"
            else:
                output_filename = f"paper_qa_results_{timestamp}.csv"
        
        # Save CSV
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✅ Results saved to: {output_path}")
            
            # Show preview
            print(f"\nResults preview:")
            print(f"{'='*60}")
            for i, row in df.head(2).iterrows():
                print(f"\n📄 PDF: {row['pdf_filename']}")
                # Display all question-answer pairs
                q_cols = [col for col in df.columns if col.startswith('question_')]
                for q_col in q_cols:
                    a_col = q_col.replace('question_', 'answer_')
                    if q_col in row and a_col in row:
                        print(f"  ❓ {row[q_col][:50]}...")
                        print(f"  💡 {row[a_col][:100]}...")
            print(f"\n{'='*60}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return ""


def main():
    """Main function: Process command line arguments and execute batch paper QA"""
    parser = argparse.ArgumentParser(
        description="Batch Paper Question Answering Tool - Ask the same question to all PDFs in a folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  # Mode 1: Single question
  python batch_paper_qa.py -f pdfs/llm_hallucination -q "What are the main contributions?" -p 5
  
  # Mode 2: Multiple questions from file
  python batch_paper_qa.py -f pdfs/llm_hallucination -qf questions.txt -p 5
  
  # Chinese question
  python batch_paper_qa.py -f pdfs/llm_code_generation -q "这篇论文使用了什么研究方法？" -p 10
  
  # Specify output filename
  python batch_paper_qa.py -f pdfs/transformer -q "What datasets were used?" -p 3 -o custom.csv

Questions file format (questions.txt):
  What are the main contributions of this paper?
  What datasets were used in the experiments?
  What is the main research method?
        """
    )
    
    parser.add_argument(
        "--folder", "-f",
        type=str,
        required=True,
        help="PDF folder path (e.g., pdfs/llm_hallucination)"
    )
    
    # Question input - mutually exclusive group
    question_group = parser.add_mutually_exclusive_group(required=True)
    question_group.add_argument(
        "--question", "-q",
        type=str,
        help="Single question to ask (same question for all PDFs)"
    )
    question_group.add_argument(
        "--questions-file", "-qf",
        type=str,
        help="Path to text file containing multiple questions (one per line)"
    )
    
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=5,
        help="Maximum number of pages to read from each PDF (default: 5)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output CSV filename (optional, auto-generated with timestamp by default)"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=2.0,
        help="Delay in seconds between API calls (default: 2.0)"
    )
    
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="OpenAI API key (optional, if not set in file)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.pages <= 0:
        print("❌ Error: Number of pages must be greater than 0")
        sys.exit(1)
    
    # Load questions based on input mode
    questions = []
    if args.question:
        # Mode 1: Single question from -q parameter
        if not args.question.strip():
            print("❌ Error: Question cannot be empty")
            sys.exit(1)
        questions = [args.question]
    elif args.questions_file:
        # Mode 2: Multiple questions from file
        if not os.path.exists(args.questions_file):
            print(f"❌ Error: Questions file not found: {args.questions_file}")
            sys.exit(1)
        
        try:
            with open(args.questions_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
            
            if not questions:
                print(f"❌ Error: No questions found in file: {args.questions_file}")
                sys.exit(1)
            
            print(f"📋 Loaded {len(questions)} questions from file: {args.questions_file}")
        except Exception as e:
            print(f"❌ Error reading questions file: {e}")
            sys.exit(1)
    
    # Execute batch QA
    try:
        print(f"\n{'='*60}")
        print(f"📚 Batch Paper Question Answering Tool")
        print(f"{'='*60}")
        print(f"📁 Folder: {args.folder}")
        print(f"❓ Questions: {len(questions)}")
        if len(questions) == 1:
            print(f"   {questions[0]}")
        else:
            for idx, q in enumerate(questions[:3], 1):
                print(f"   Q{idx}: {q[:70]}{'...' if len(q) > 70 else ''}")
            if len(questions) > 3:
                print(f"   ... and {len(questions) - 3} more questions")
        print(f"📄 Pages to read: {args.pages}")
        print(f"🤖 Model: gpt-3.5-turbo")
        print(f"⏱️  Delay: {args.delay} seconds")
        print(f"{'='*60}\n")
        
        # Create processor
        processor = BatchPaperQuestionAnswering(api_key=args.api_key)
        
        # Process folder
        df_results = processor.process_folder(
            folder_path=args.folder,
            questions=questions,
            max_pages=args.pages,
            delay=args.delay,
            model="gpt-3.5-turbo"  # Fixed model
        )
        
        # Save results
        if not df_results.empty:
            # Extract folder name from path for filename
            folder_name = os.path.basename(args.folder.rstrip('/'))
            output_path = processor.save_results(
                df_results, 
                output_filename=args.output,
                folder_name=folder_name
            )
            
            if output_path:
                print(f"\n✅ All done!")
                print(f"📊 Results file: {output_path}")
        else:
            print("\n❌ Failed to generate results")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
