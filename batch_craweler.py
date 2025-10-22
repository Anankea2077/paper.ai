#!/usr/bin/env python3
"""
Complete workflow: Crawl papers + Optional Translate abstracts + Optional Classify papers
Usage: python test_complete_workflow.py --keywords <keywords> --n <N> [--translate <language>] [--classify]
Example: python test_complete_workflow.py --keywords "llm hallucination" --n 5 --translate zh-cn --classify
"""

import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler import PaperCrawler
from paper_detail_crawler import PaperDetailCrawler
from advanced_processor import AdvancedProcessor
from paper_metadata_api import PaperMetadataAPI

# Template for classification
TEMPLATE_NAME = "classification_template"

# 📁 OUTPUT FILE CONFIGURATION 📁
# Dynamic output CSV file name based on keywords
def get_output_filename(keywords_str):
    """Generate output filename based on keywords"""
    keywords_safe = '_'.join(keywords_str.split()).replace(' ', '_')
    return f"papers_{keywords_safe}.csv"

def complete_workflow(keywords_str, n_papers, translate_language=None, classify=False, download_pdfs=False, get_metadata=False):
    """Complete workflow: crawl + optional translate + optional classify"""
    
    # Parse keywords and generate output filename
    keywords = keywords_str.split()
    output_filename = get_output_filename(keywords_str)
    
    print("=" * 60)
    print("Complete Workflow: Crawl Papers")
    if translate_language:
        print(f" + Translate to {translate_language}")
    if classify:
        print(" + LLM Classification")
    if download_pdfs:
        print(" + Download PDFs")
    if get_metadata:
        print(" + Get Paper Metadata (Year & Citation Count)")
    print("=" * 60)
    
    print(f"Keywords: {keywords_str}")
    print(f"Number of papers: {n_papers}")
    if translate_language:
        print(f"Translation: {translate_language}")
    else:
        print("Translation: Disabled")
    print(f"Classification: {'Enabled' if classify else 'Disabled'}")
    print(f"PDF Download: {'Enabled' if download_pdfs else 'Disabled'}")
    print(f"Metadata Retrieval: {'Enabled' if get_metadata else 'Disabled'}")
    print(f"Output file: {output_filename}")
    
    # 【Step 1】: Get paper URLs
    print(f"\n【Step 1】: Getting paper URLs from search")
    print("-" * 40)
    
    main_crawler = PaperCrawler(keywords, N=n_papers)
    paper_urls = main_crawler.extract_paper_urls()
    
    print(f"Found {len(paper_urls)} paper URLs:")
    for i, url in enumerate(paper_urls, 1):
        print(f"  {i}. {url}")
    
    if not paper_urls:
        print("❌ No paper URLs found. Exiting.")
        return
    
    # 【Step 2】: Extract detailed information
    print(f"\n【Step 2】: Extracting detailed information")
    print("-" * 40)
    
    detail_crawler = PaperDetailCrawler()
    print(f"Crawling {len(paper_urls)} papers with 2-second delay...")
    
    all_details = detail_crawler.crawl_multiple_papers(paper_urls, delay=2.0)
    
    print(f"✅ Successfully crawled {len(all_details)} papers")
    
    # Convert to DataFrame for processing
    import pandas as pd
    df = pd.DataFrame(all_details)
    
    if df.empty:
        print("❌ No data to process")
        return
    
    df_final = df
    
    # 【Step 2.5】: Download PDFs (if requested)
    if download_pdfs:
        print(f"\n【Step 2.5】: Downloading PDFs")
        print("-" * 40)
        
        # Filter error rows and fill empty values before converting DataFrame to records to avoid type errors from NaN
        df_for_pdf = df.copy()
        if 'error' in df_for_pdf.columns:
            df_for_pdf = df_for_pdf[df_for_pdf['error'].isna()]
        for col in ['pdf_url', 'title']:
            if col in df_for_pdf.columns:
                df_for_pdf[col] = df_for_pdf[col].fillna('')
        # Convert DataFrame back to list for PDF download
        papers_list = df_for_pdf.to_dict('records')
        
        # Download PDFs using PaperCrawler
        main_crawler = PaperCrawler(keywords, N=n_papers)
        papers_with_pdfs = main_crawler.download_pdfs_from_papers(papers_list, delay=2.0)
        
        # Convert back to DataFrame with pdf_path column
        df_final = pd.DataFrame(papers_with_pdfs)
        
        # Count downloaded PDFs
        pdf_count = sum(1 for paper in papers_with_pdfs if paper.get('pdf_path'))
        print(f"✅ Downloaded {pdf_count} PDFs out of {len(papers_with_pdfs)} papers")
    else:
        print(f"\n【Step 2.5】: PDF Download skipped")
        print("-" * 40)
        print("PDF download disabled by parameter")
    
    # 【Step 3】: Translate abstracts (if requested)
    if translate_language:
        print(f"\n【Step 3】: Translating abstracts to {translate_language}")
        print("-" * 40)
        
        processor = AdvancedProcessor()
        
        print(f"Translating {len(df)} abstracts...")
        df_translated = processor.translate_abstracts(df, target_language=translate_language, delay=2.0)
        
        print("✅ Translation completed!")
        df_final = df_translated
    else:
        print(f"\n【Step 3】: Translation skipped")
        print("-" * 40)
        print("Translation disabled by parameter")
    
    # 【Step 4】: Get paper metadata (if requested)
    if get_metadata:
        print(f"\n【Step 4】: Getting paper metadata (Year & Citation Count)")
        print("-" * 40)
        
        api = PaperMetadataAPI()
        
        print(f"Fetching metadata for {len(df_final)} papers...")
        print("Note: This will make API calls to Google Scholar, Semantic Scholar, and CrossRef.")
        
        # Add metadata columns
        df_final['Year'] = None
        df_final['Citation_Count'] = 0
        df_final['Metadata_Source'] = 'not_found'
        
        for i, (_, row) in enumerate(df_final.iterrows()):
            title = row['title']
            print(f"Processing paper {i+1}/{len(df_final)}: {title[:50]}...")
            
            metadata = api.get_paper_metadata(title)
            if metadata:
                df_final.at[i, 'Year'] = metadata.get('year')
                df_final.at[i, 'Citation_Count'] = metadata.get('citation_count', 0)
                df_final.at[i, 'Metadata_Source'] = metadata.get('source', '')
            
            # Add delay to avoid rate limiting (conservative for Google Scholar with randomization)
            if i < len(df_final) - 1:
                import time
                import random
                base_delay = 3.0  # Base 3 second delay for Google Scholar
                random_delay = random.uniform(0.5, 2.0)  # Add 0.5-2 seconds randomization
                total_delay = base_delay + random_delay
                print(f"Waiting {total_delay:.1f} seconds before next request...")
                time.sleep(total_delay)
        
        found_count = len(df_final[df_final['Metadata_Source'] != 'not_found'])
        print(f"✅ Metadata retrieval completed! Found metadata for {found_count}/{len(df_final)} papers")
        
        if found_count > 0:
            avg_citations = df_final[df_final['Citation_Count'] > 0]['Citation_Count'].mean()
            print(f"Average citation count: {avg_citations:.1f}")
    else:
        print(f"\n【Step 4】: Metadata retrieval skipped")
        print("-" * 40)
        print("Metadata retrieval disabled by parameter")
    
    # 【Step 5】: Classify papers (if requested)
    if classify:
        print(f"\n【Step 5】: Classifying papers using OpenAI API")
        print("-" * 40)
        
        processor = AdvancedProcessor()
        
        print(f"Classifying {len(df_final)} papers with keywords: {keywords}")
        print("Note: This will make API calls to OpenAI. Make sure you have sufficient credits.")
        
        df_classified = processor.classify_papers(df_final, keywords, num_categories=4, delay=3.0, template_name=TEMPLATE_NAME)
        print("✅ Classification completed!")
        df_final = df_classified
    else:
        print(f"\n【Step 5】: Classification skipped")
        print("-" * 40)
        print("Classification disabled by parameter")
    
    # Show final results preview
    print(f"\nFinal results preview:")
    try:
        for i, (_, row) in enumerate(df_final.head(2).iterrows(), 1):
            print(f"  Paper {i}:")
            # Safely handle fields that may be NaN
            title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
            print(f"    Title: {title[:50]}...")
            
            if 'abstract_translate' in row and pd.notna(row['abstract_translate']):
                abstract_translate = str(row['abstract_translate'])
                print(f"    Translated Abstract: {abstract_translate[:60]}...")
            elif 'abstract' in row and pd.notna(row['abstract']):
                abstract = str(row['abstract'])
                print(f"    Original Abstract: {abstract[:60]}...")
            
            if 'category' in row and pd.notna(row['category']):
                print(f"    Category: {row['category']}")
            if 'Year' in row and pd.notna(row['Year']):
                print(f"    Year: {row['Year']}")
            if 'Citation_Count' in row and pd.notna(row['Citation_Count']) and row['Citation_Count'] > 0:
                print(f"    Citation Count: {row['Citation_Count']}")
            if 'pdf_path' in row and pd.notna(row['pdf_path']):
                print(f"    PDF: {row['pdf_path']}")
    except Exception as e:
        print(f"⚠️  Preview error (but will still save CSV): {e}")
    
    # 【Step 6】: Save final results
    print(f"\n【Step 6】: Saving final results")
    print("-" * 40)
    
    # Ensure CSV file can be saved no matter what
    output_path = None
    try:
        # First try using AdvancedProcessor to save
        processor = AdvancedProcessor()
        output_path = processor.save_processed_csv(df_final, output_filename)
    except Exception as e:
        print(f"⚠️  AdvancedProcessor save failed: {e}")
        print("🔄 Trying direct CSV save...")
        
        # If AdvancedProcessor fails, save CSV directly
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_dir = os.path.join(current_dir, 'outputs')
            os.makedirs(outputs_dir, exist_ok=True)
            
            output_path = os.path.join(outputs_dir, output_filename)
            
            # Clean NaN values in DataFrame
            df_clean = df_final.copy()
            for col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna('')
            
            # Save directly as CSV
            df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✅ Direct CSV save successful: {output_path}")
            
        except Exception as e2:
            print(f"❌ Direct CSV save also failed: {e2}")
            print("🔄 Trying basic CSV save with minimal data...")
            
            # Last fallback: save only basic fields
            try:
                # Redefine outputs_dir
                current_dir = os.path.dirname(os.path.abspath(__file__))
                outputs_dir = os.path.join(current_dir, 'outputs')
                os.makedirs(outputs_dir, exist_ok=True)
                
                basic_df = df_final[['title', 'url']].copy() if 'title' in df_final.columns and 'url' in df_final.columns else df_final.iloc[:, :2]
                basic_df = basic_df.fillna('')
                basic_output_path = os.path.join(outputs_dir, f"basic_{output_filename}")
                basic_df.to_csv(basic_output_path, index=False, encoding='utf-8-sig')
                output_path = basic_output_path
                print(f"✅ Basic CSV saved: {output_path}")
            except Exception as e3:
                print(f"❌ All save methods failed: {e3}")
                output_path = None
    
    if output_path and os.path.exists(output_path):
        print(f"✅ Final results saved to: {output_path}")
        
        # Show CSV content preview
        try:
            print(f"\nCSV content preview:")
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                if lines:
                    print(f"  Header: {lines[0].strip()}")
                    for i, line in enumerate(lines[1:3], 1):  # Show first 2 data lines
                        print(f"  Row {i}: {line.strip()[:80]}...")
        except Exception as e:
            print(f"⚠️  Preview error: {e}")
    else:
        print("❌ Failed to save results - no output file created")
    
    print(f"\n" + "=" * 60)
    print("Complete workflow finished!")
    print(f"📁 Output file: {output_filename}")
    print("=" * 60)

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Complete workflow: Crawl papers with optional translation and classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic crawling only
  python test_complete_workflow.py --keywords "llm hallucination" --n 5

  # Crawl + Translate
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --translate zh-cn

  # Crawl + Classify
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --classify

  # Crawl + Translate + Classify (full workflow)
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --translate zh-cn --classify

  # Crawl + Download PDFs
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --download-pdfs

  # Crawl + Get Metadata (Year & Citation Count)
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --get-metadata

  # Full workflow with all features
  python test_complete_workflow.py --keywords "llm hallucination" --n 5 --translate zh-cn --classify --download-pdfs --get-metadata

  # Short form
  python test_complete_workflow.py -k "llm hallucination" -n 5 -t zh-cn -c -d -m

Supported languages: zh-cn, zh-tw, es, fr, de, ja, ko, ru, ar, hi, pt, it, nl, sv, da, no, fi
        """
    )
    
    parser.add_argument(
        "--keywords", "-k",
        type=str,
        required=True,
        help="Search keywords (space-separated string, e.g., 'llm hallucination')"
    )
    
    parser.add_argument(
        "--n", "-n",
        type=int,
        required=True,
        help="Number of papers to crawl (first N papers)"
    )
    
    parser.add_argument(
        "--translate", "-t",
        type=str,
        help="Target language code for translation (e.g., zh-cn, es, fr). If not provided, translation is skipped."
    )
    
    parser.add_argument(
        "--classify", "-c",
        action="store_true",
        help="Enable LLM classification (requires OpenAI API key)"
    )
    
    parser.add_argument(
        "--download-pdfs", "-d",
        action="store_true",
        help="Download arXiv PDFs to pdfs/keywords folder"
    )
    
    parser.add_argument(
        "--get-metadata", "-m",
        action="store_true",
        help="Get paper metadata (Year & Citation Count) from Google Scholar, Semantic Scholar, and CrossRef"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.n <= 0:
        print("❌ Error: Number of papers must be positive")
        sys.exit(1)
    
    if not args.keywords.strip():
        print("❌ Error: Keywords cannot be empty")
        sys.exit(1)
    
    # Run the workflow
    try:
        complete_workflow(args.keywords, args.n, args.translate, args.classify, args.download_pdfs, args.get_metadata)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
