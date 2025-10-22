import pandas as pd
import requests
from typing import List, Dict, Optional
import time
import os
import urllib.parse
import json
from openai import OpenAI
import sys

# Add api directory to path to import keys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api'))

# Load API keys
try:
    from keys import OPENAI_API_KEY as API_KEY_FROM_FILE
except ImportError:
    API_KEY_FROM_FILE = None
    print("⚠️  Warning: api/keys.py not found. Please create it from api/keys.example.py")

class AdvancedProcessor:
    """
    Advanced processing functions for paper data
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the advanced processor
        
        Args:
            openai_api_key: OpenAI API key (optional, will use the constant above if not provided)
        """
        # Set up OpenAI client - priority: parameter > api/keys.py > environment variable
        api_key = None
        if openai_api_key:
            api_key = openai_api_key
            print(f"✅ Using API key from parameter")
        elif API_KEY_FROM_FILE and not API_KEY_FROM_FILE.startswith("sk-proj-xxxx"):
            api_key = API_KEY_FROM_FILE
            print(f"✅ Using API key from api/keys.py")
        elif os.getenv('OPENAI_API_KEY'):
            api_key = os.getenv('OPENAI_API_KEY')
            print(f"✅ Using API key from environment variable")
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print(f"✅ OpenAI API key set successfully")
        else:
            print("⚠️  WARNING: OpenAI API key not found!")
            print("   1. Copy api/keys.example.py to api/keys.py and add your key")
            print("   2. Or set OPENAI_API_KEY environment variable")
            print("   3. Or pass openai_api_key parameter")
            print("   Get your key from: https://platform.openai.com/api-keys")
            self.client = None
        
        # No complex prompt manager needed
    
    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load prompt template from prompts directory
        
        Args:
            template_name: Name of the template file (without .py extension)
            
        Returns:
            Template string
        """
        try:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_dir = os.path.join(current_dir, '..', 'prompts')
            template_path = os.path.join(prompts_dir, f"{template_name}.py")
            
            # Read and execute the template file
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create a namespace to execute the template
            namespace = {}
            exec(template_content, namespace)
            
            # Get the template variable
            template_var = f"{template_name.upper().replace('_', '_')}_TEMPLATE"
            if template_var in namespace:
                return namespace[template_var]
            else:
                # Fallback: try common naming patterns
                for key in namespace.keys():
                    if key.endswith('_TEMPLATE'):
                        return namespace[key]
                
                raise KeyError(f"Template variable not found in {template_path}")
                
        except Exception as e:
            print(f"⚠️  Error loading template {template_name}: {e}")
            return None
    
    def _translate_text(self, text: str, target_lang: str = 'zh') -> str:
        """
        Translate text using Google Translate API (free version)
        
        Args:
            text: Text to translate
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        try:
            # Google Translate free API endpoint
            url = "https://translate.googleapis.com/translate_a/single"
            
            params = {
                'client': 'gtx',
                'sl': 'auto',  # source language (auto-detect)
                'tl': target_lang,  # target language
                'dt': 't',
                'q': text
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract translated text
            if result and result[0]:
                translated_text = ''.join([item[0] for item in result[0] if item[0]])
                return translated_text
            else:
                return text
                
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation failed: {str(e)}"
    
    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load paper data from CSV file
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            DataFrame containing paper data
        """
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            print(f"Loaded {len(df)} papers from {csv_path}")
            return df
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return pd.DataFrame()
    
    def translate_abstracts(self, df: pd.DataFrame, target_language: str = 'zh-cn', 
                          delay: float = 1.0) -> pd.DataFrame:
        """
        Translate abstracts to specified language
        
        Args:
            df: DataFrame containing paper data
            target_language: Target language code (e.g., 'zh-cn' for Chinese, 'es' for Spanish)
            delay: Delay between translation requests to avoid rate limiting
            
        Returns:
            DataFrame with added 'abstract_translate' column
        """
        if df.empty:
            print("DataFrame is empty")
            return df
        
        # Create a copy to avoid modifying original
        df_result = df.copy()
        
        # Initialize translation column
        df_result['abstract_translate'] = ''
        
        print(f"Translating {len(df_result)} abstracts to {target_language}...")
        
        for index, row in df_result.iterrows():
            try:
                abstract = str(row['abstract'])
                
                # Skip empty abstracts
                if pd.isna(abstract) or abstract.strip() == '':
                    print(f"Paper {index + 1}: Skipping empty abstract")
                    continue
                
                print(f"Paper {index + 1}/{len(df_result)}: Translating...")
                
                # Translate the abstract
                translation = self._translate_text(abstract, target_language)
                df_result.at[index, 'abstract_translate'] = translation
                
                # Rate limiting
                if index < len(df_result) - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error translating paper {index + 1}: {e}")
                df_result.at[index, 'abstract_translate'] = f"Translation failed: {str(e)}"
        
        print("Translation completed!")
        return df_result
    
    def save_processed_csv(self, df: pd.DataFrame, filename: str, 
                          outputs_dir: str = None) -> str:
        """
        Save processed DataFrame to CSV
        
        Args:
            df: DataFrame to save
            filename: Output filename
            outputs_dir: Output directory (default: ../outputs)
            
        Returns:
            Path to saved CSV file
        """
        if outputs_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            outputs_dir = os.path.join(current_dir, '..', 'outputs')
        
        # Create outputs directory if it doesn't exist
        os.makedirs(outputs_dir, exist_ok=True)
        
        csv_path = os.path.join(outputs_dir, filename)
        
        try:
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Processed data saved to: {csv_path}")
            return csv_path
        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return ""
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get human-readable language name from code
        
        Args:
            lang_code: Language code (e.g., 'zh-cn', 'es', 'fr')
            
        Returns:
            Human-readable language name
        """
        language_names = {
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'pt': 'Portuguese',
            'it': 'Italian',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish'
        }
        return language_names.get(lang_code, lang_code.upper())
    
    def process_csv_with_translation(self, input_csv: str, output_csv: str = None, 
                                   target_language: str = 'zh-cn', 
                                   delay: float = 1.0) -> str:
        """
        Complete workflow: load CSV, translate abstracts, save results
        
        Args:
            input_csv: Path to input CSV file
            output_csv: Path to output CSV file (auto-generated if None)
            target_language: Target language for translation
            delay: Delay between translation requests
            
        Returns:
            Path to output CSV file
        """
        # Load data
        df = self.load_csv(input_csv)
        if df.empty:
            return ""
        
        # Generate output filename if not provided
        if output_csv is None:
            base_name = os.path.splitext(os.path.basename(input_csv))[0]
            lang_name = target_language.replace('-', '_')
            output_csv = f"{base_name}_translated_{lang_name}.csv"
        
        # Translate abstracts
        df_translated = self.translate_abstracts(df, target_language, delay)
        
        # Save results
        output_path = self.save_processed_csv(df_translated, output_csv)
        
        return output_path
    
    def classify_papers(self, df: pd.DataFrame, keywords: List[str], 
                       num_categories: int = 4, delay: float = 2.0, 
                       template_name: str = "classification_template") -> pd.DataFrame:
        """
        Classify papers using OpenAI API based on all papers' content (unsupervised)
        
        Args:
            df: DataFrame containing paper data
            keywords: List of keywords used for search (as hints for classification)
            num_categories: Number of categories to create (default: 4)
            delay: Delay between API calls to avoid rate limiting
            template_name: Name of the prompt template to use (default: classification_template)
            
        Returns:
            DataFrame with added 'category' column
        """
        if df.empty:
            print("DataFrame is empty")
            return df
        
        if not self.client:
            print("OpenAI API key not available. Skipping classification.")
            return df
        
        # Create a copy to avoid modifying original
        df_result = df.copy()
        
        # Initialize category column
        df_result['category'] = ''
        
        # Prepare context for classification
        keywords_str = ', '.join(keywords)
        
        print(f"Classifying {len(df_result)} papers using OpenAI API...")
        print(f"Keywords context: {keywords_str}")
        print("Using unsupervised classification - LLM will analyze all papers together")
        
        # Prepare papers info for batch classification
        papers_info = ""
        for index, row in df_result.iterrows():
            title = str(row['title'])
            llm_summary = str(row['llm_summary'])
            
            # Skip empty summaries
            if pd.isna(llm_summary) or llm_summary.strip() == '':
                print(f"Paper {index + 1}: Skipping empty summary")
                continue
            
            papers_info += f"Title: {title}\nSummary: {llm_summary}\n\n"
        
        if not papers_info.strip():
            print("No valid papers to classify")
            return df_result
        
        # Create classification prompt for all papers
        prompt = self._create_batch_classification_prompt(
            papers_info, keywords_str, num_categories, template_name
        )
        
        print("Sending all papers to LLM for classification...")
        
        # Call OpenAI API once for all papers
        response = self._call_openai_api(prompt)
        
        # Parse the JSON response
        try:
            import json
            # Extract JSON from response (in case it's wrapped in markdown)
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
            else:
                json_str = response
            
            classification_result = json.loads(json_str)
            
            # Extract classifications
            classifications = classification_result.get('classifications', {})
            categories = classification_result.get('categories', {})
            
            print(f"✅ Classification completed!")
            print(f"Created {len(categories)} categories:")
            for cat_name, cat_desc in categories.items():
                print(f"  - {cat_name}: {cat_desc}")
            
            # Assign categories to papers
            for index, row in df_result.iterrows():
                title = str(row['title'])
                if title in classifications:
                    df_result.at[index, 'category'] = classifications[title]
                else:
                    df_result.at[index, 'category'] = "Unclassified"
            
        except Exception as e:
            print(f"Error parsing classification response: {e}")
            print(f"Raw response: {response[:200]}...")
            
            # Fallback: assign error to all papers
            for index in df_result.index:
                df_result.at[index, 'category'] = f"Classification parsing failed: {str(e)}"
        
        print("Classification completed!")
        return df_result
    
    def _create_batch_classification_prompt(self, papers_info: str, keywords: str, 
                                          num_categories: int, 
                                          template_name: str = "classification_template") -> str:
        """
        Create a prompt for batch paper classification
        
        Args:
            papers_info: Combined information of all papers
            keywords: Search keywords as context
            num_categories: Number of categories to create
            template_name: Name of the template to use
            
        Returns:
            Formatted prompt string
        """
        try:
            # Load template
            template = self._load_prompt_template(template_name)
            if template:
                return template.format(
                    papers_info=papers_info,
                    keywords=keywords,
                    num_categories=num_categories
                )
        except Exception as e:
            print(f"⚠️  Error loading prompt template: {e}")
        
        # Fallback to hardcoded prompt
        print("   Falling back to default prompt...")
        return f"""You are an expert academic paper classifier. Analyze the following papers and classify them into meaningful categories.

Context keywords: {keywords}

Papers to classify:
{papers_info}

Please analyze all papers and create {num_categories} categories based on their content. Return the result in JSON format:

{{
  "categories": {{
    "Category_1": "Description",
    "Category_2": "Description"
  }},
  "classifications": {{
    "Title_1": "Category_1",
    "Title_2": "Category_2"
  }}
}}"""

    def _create_classification_prompt(self, title: str, summary: str, 
                                    keywords: str, num_categories: int, 
                                    template_name: str = "classification_template") -> str:
        """
        Create a prompt for paper classification
        
        Args:
            title: Paper title
            summary: LLM summary of the paper
            keywords: Search keywords as context
            num_categories: Number of categories to create
            template_name: Name of the template to use
            
        Returns:
            Formatted prompt string
        """
        try:
            # Load template
            template = self._load_prompt_template(template_name)
            if template:
                return template.format(
                    title=title,
                    summary=summary,
                    keywords=keywords,
                    num_categories=num_categories
                )
        except Exception as e:
            print(f"⚠️  Error loading prompt template: {e}")
        
        # Fallback to hardcoded prompt
        print("   Falling back to default prompt...")
        return f"""You are an expert in academic paper classification. Based on the paper information below, classify this paper into one of {num_categories} categories.

Context keywords from search: {keywords}

Paper Title: {title}
Paper Summary: {summary}

Please classify this paper into ONE of these {num_categories} categories. Return only the category name (3-5 words maximum), nothing else.

Examples of good categories:
- "LLM Hallucination Detection"
- "Transformer Architecture"
- "Attention Mechanisms"
- "Neural Network Training"
- "Natural Language Processing"
- "Computer Vision Applications"

Category:"""
    
    def _call_openai_api(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Call OpenAI API for classification
        
        Args:
            prompt: Classification prompt
            model: OpenAI model to use
            
        Returns:
            Classification result
        """
        if not self.client:
            return "API Error: OpenAI client not initialized"
        
        try:
            # Use more tokens for batch classification
            max_tokens = 2000 if len(prompt) > 1000 else 100
            
            # Call OpenAI API (new version)
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert academic paper classifier. Provide accurate classifications in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            return result
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"API Error: {str(e)}"
    
    def process_csv_with_classification(self, input_csv: str, keywords: List[str],
                                      output_csv: str = None, num_categories: int = 4,
                                      delay: float = 2.0, template_name: str = "classification_template") -> str:
        """
        Complete workflow: load CSV, classify papers, save results
        
        Args:
            input_csv: Path to input CSV file
            keywords: Search keywords for classification context
            output_csv: Path to output CSV file (auto-generated if None)
            num_categories: Number of categories to create
            delay: Delay between API calls
            
        Returns:
            Path to output CSV file
        """
        # Load data
        df = self.load_csv(input_csv)
        if df.empty:
            return ""
        
        # Generate output filename if not provided
        if output_csv is None:
            base_name = os.path.splitext(os.path.basename(input_csv))[0]
            output_csv = f"{base_name}_classified.csv"
        
        # Classify papers
        df_classified = self.classify_papers(df, keywords, num_categories, delay, template_name)
        
        # Save results
        output_path = self.save_processed_csv(df_classified, output_csv)
        
        return output_path
