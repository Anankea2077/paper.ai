"""
Classification prompt template for unsupervised paper classification
"""

CLASSIFICATION_TEMPLATE = """You are an expert academic paper classifier. Your task is to analyze the following research papers and classify them into meaningful categories based on their content and themes.

**Context Keywords:** {keywords}

**Papers to Classify:**
{papers_info}

**Classification Task:**
1. Analyze all the papers above and identify the main themes and research directions
2. Create meaningful categories based on the actual content of these papers (not predefined categories)
3. Assign each paper to the most appropriate category
4. Aim for {num_categories} categories, but adjust if the content suggests a different number

**Instructions:**
- Read through all papers to understand the overall research landscape
- Identify natural groupings based on research focus, methodology, or application
- Create category names that accurately describe the themes you observe
- Each paper should be assigned to exactly one category
- Categories should be mutually exclusive and collectively exhaustive

**Response Format:**
Return your classification in the following JSON format:
```json
{{
  "categories": {{
    "Category_Name_1": "Brief description of this category",
    "Category_Name_2": "Brief description of this category",
    ...
  }},
  "classifications": {{
    "Title_1": "Category_Name_1",
    "Title_2": "Category_Name_2",
    ...
  }}
}}
```

Please ensure the JSON is valid and complete."""
