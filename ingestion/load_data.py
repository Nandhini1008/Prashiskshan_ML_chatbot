"""
Data loading module for ingesting documents from various sources.
Handles loading of company data, FAQs, and college documents.
"""

import os
from typing import List, Dict, Any
import json
from pathlib import Path

class DataLoader:
    """Loads documents from the data directory."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Root directory containing data files
        """
        self.data_dir = data_dir
        self.companies_dir = os.path.join(data_dir, "companies")
        self.faqs_dir = os.path.join(data_dir, "faqs")
        self.college_docs_dir = os.path.join(data_dir, "college_docs")
    
    def load_text_file(self, filepath: str) -> str:
        """
        Load content from a text file.
        
        Args:
            filepath: Path to the text file
            
        Returns:
            Content of the file as string
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading file {filepath}: {e}")
            return ""
    
    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load content from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Parsed JSON content as dictionary
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file {filepath}: {e}")
            return {}
    
    def load_company_documents(self) -> List[Dict[str, Any]]:
        """
        Load all company-related documents.
        
        Returns:
            List of documents with metadata
        """
        documents = []
        
        if not os.path.exists(self.companies_dir):
            print(f"Companies directory not found: {self.companies_dir}")
            return documents
        
        for filename in os.listdir(self.companies_dir):
            filepath = os.path.join(self.companies_dir, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            if filename.endswith('.txt'):
                content = self.load_text_file(filepath)
                company_name = Path(filename).stem
                
                documents.append({
                    "content": content,
                    "metadata": {
                        "company": company_name,
                        "document_type": "company_info",
                        "source": filepath
                    }
                })
            
            elif filename.endswith('.json'):
                data = self.load_json_file(filepath)
                if data:
                    company_name = data.get("company_name", Path(filename).stem)
                    content = json.dumps(data, indent=2)
                    
                    documents.append({
                        "content": content,
                        "metadata": {
                            "company": company_name,
                            "document_type": "company_info",
                            "source": filepath
                        }
                    })
        
        return documents
    
    def load_faq_documents(self) -> List[Dict[str, Any]]:
        """
        Load all FAQ documents.
        
        Returns:
            List of FAQ documents with metadata
        """
        documents = []
        
        if not os.path.exists(self.faqs_dir):
            print(f"FAQs directory not found: {self.faqs_dir}")
            return documents
        
        for filename in os.listdir(self.faqs_dir):
            filepath = os.path.join(self.faqs_dir, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            if filename.endswith('.txt'):
                content = self.load_text_file(filepath)
                
                documents.append({
                    "content": content,
                    "metadata": {
                        "company": "general",
                        "document_type": "faq",
                        "source": filepath
                    }
                })
            
            elif filename.endswith('.json'):
                data = self.load_json_file(filepath)
                if data and "faqs" in data:
                    for faq in data["faqs"]:
                        content = f"Q: {faq.get('question', '')}\nA: {faq.get('answer', '')}"
                        
                        documents.append({
                            "content": content,
                            "metadata": {
                                "company": "general",
                                "document_type": "faq",
                                "source": filepath
                            }
                        })
        
        return documents
    
    def load_college_documents(self) -> List[Dict[str, Any]]:
        """
        Load all college-related documents.
        
        Returns:
            List of college documents with metadata
        """
        documents = []
        
        if not os.path.exists(self.college_docs_dir):
            print(f"College docs directory not found: {self.college_docs_dir}")
            return documents
        
        for filename in os.listdir(self.college_docs_dir):
            filepath = os.path.join(self.college_docs_dir, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            if filename.endswith('.txt'):
                content = self.load_text_file(filepath)
                
                documents.append({
                    "content": content,
                    "metadata": {
                        "company": "college",
                        "document_type": "college_policy",
                        "source": filepath
                    }
                })
        
        return documents
    
    def load_all_documents(self) -> List[Dict[str, Any]]:
        """
        Load all documents from all sources.
        
        Returns:
            Combined list of all documents with metadata
        """
        all_documents = []
        
        all_documents.extend(self.load_company_documents())
        all_documents.extend(self.load_faq_documents())
        all_documents.extend(self.load_college_documents())
        
        print(f"Loaded {len(all_documents)} documents in total")
        return all_documents
