import boto3
import json
from typing import Dict, Any, List

class ClaudeClient:
    def __init__(self, region_name: str = "us-west-2"):
        """Initialize Claude client for invoice processing."""
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "anthropic.claude-3-5-haiku-20241022-v1:0" 
    
    def format_extracted_text(self, raw_text: str, document_type: str = "invoice") -> Dict[str, Any]:
        """
        Use Claude to format raw Textract output into structured data.
        
        Args:
            raw_text: Raw text from Textract
            document_type: Type of document (invoice, receipt, etc.)
            
        Returns:
            Structured data dictionary
        """
        prompt = f"""
        You are an expert at extracting structured data from {document_type} text.
        
        Please analyze this raw text extracted from a document and return a JSON object with the following fields:
        - vendor_name: Company/vendor name
        - invoice_number: Invoice or reference number
        - date: Date (in YYYY-MM-DD format)
        - total_amount: Total amount (as number)
        - currency: Currency code (USD, etc.)
        - line_items: Array of items with description, quantity, unit_price, total
        - tax_amount: Tax amount if present
        - payment_terms: Payment terms if specified
        - confidence_score: Your confidence in the extraction (0-1)
        
        If a field cannot be determined, use null. Be as accurate as possible. Some fields may not be present in the text.
        Also, the fields may have different names in the text, so you need to be able to handle that.
        
        Raw text:
        {raw_text}
        
        Return only valid JSON:
        """
        
        return self._call_claude(prompt)
    
    def validate_extraction(self, extracted_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Use Claude to validate and improve extracted data.
        
        Args:
            extracted_data: Previously extracted structured data
            raw_text: Original raw text for reference
            
        Returns:
            Validation results with corrections
        """
        prompt = f"""
        Please review this extracted data against the original text and provide validation.
        
        Extracted Data:
        {json.dumps(extracted_data, indent=2)}
        
        Original Text:
        {raw_text}
        
        Return a JSON object with:
        - is_valid: boolean indicating if extraction looks correct
        - confidence_score: overall confidence (0-1)
        - corrections: object with any field corrections needed
        - warnings: array of potential issues found
        - suggestions: array of improvement suggestions
        
        Return only valid JSON:
        """
        
        return self._call_claude(prompt)
    
    def _call_claude(self, message: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Internal method to call Claude and return parsed JSON.
        
        Args:
            message: Prompt to send to Claude
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response
        """
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.1  # Low temperature for consistent formatting
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            
            response_body = json.loads(response["body"].read())
            claude_response = response_body["content"][0]["text"]
            
            # Try to parse as JSON
            try:
                return json.loads(claude_response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text with error
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": claude_response
                }
                
        except Exception as e:
            return {
                "error": f"Claude API error: {str(e)}"
            }