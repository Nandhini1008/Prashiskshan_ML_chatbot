"""
Text cleaning and preprocessing module.
Normalizes and cleans text data before chunking and embedding.
"""

import re

class TextCleaner:
    """Handles text cleaning and normalization."""
    
    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        """
        Remove extra whitespace from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()
    
    @staticmethod
    def remove_special_characters(text: str, keep_punctuation: bool = True) -> str:
        """
        Remove or normalize special characters.
        
        Args:
            text: Input text
            keep_punctuation: Whether to keep basic punctuation
            
        Returns:
            Cleaned text
        """
        if keep_punctuation:
            # Keep alphanumeric, spaces, and basic punctuation
            text = re.sub(r'[^\w\s.,!?;:()\-\[\]{}"\'/]', ' ', text)
        else:
            # Keep only alphanumeric and spaces
            text = re.sub(r'[^\w\s]', ' ', text)
        
        return text
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normalize unicode characters.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized unicode
        """
        # Replace common unicode quotes
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        # Replace em dash and en dash
        text = text.replace('\u2014', '-').replace('\u2013', '-')
        # Replace non-breaking space
        text = text.replace('\u00a0', ' ')
        
        return text
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """
        Remove URLs from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with URLs removed
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, '', text)
        return text
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """
        Remove email addresses from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with emails removed
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)
        return text
    
    def clean(self, text: str, 
              remove_urls: bool = False,
              remove_emails: bool = False,
              keep_punctuation: bool = True) -> str:
        """
        Apply all cleaning steps to text.
        
        Args:
            text: Input text
            remove_urls: Whether to remove URLs
            remove_emails: Whether to remove email addresses
            keep_punctuation: Whether to keep punctuation
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize unicode
        text = self.normalize_unicode(text)
        
        # Remove URLs if requested
        if remove_urls:
            text = self.remove_urls(text)
        
        # Remove emails if requested
        if remove_emails:
            text = self.remove_emails(text)
        
        # Remove special characters
        text = self.remove_special_characters(text, keep_punctuation)
        
        # Remove extra whitespace
        text = self.remove_extra_whitespace(text)
        
        return text
    
    def clean_document(self, document: dict) -> dict:
        """
        Clean a document dictionary.
        
        Args:
            document: Document with 'content' and 'metadata' keys
            
        Returns:
            Document with cleaned content
        """
        cleaned_doc = document.copy()
        cleaned_doc['content'] = self.clean(document['content'])
        return cleaned_doc
