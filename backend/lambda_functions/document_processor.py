# Enhanced document_processor.py with better error handling and validation

import json
import base64
import boto3
import uuid
import time
from typing import Dict, Any, Optional
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from clients.local_text_extractor import LocalTextExtractor
from clients.claude_client import ClaudeClient

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with enhanced error handling."""
        try:
            self.text_extractor = LocalTextExtractor()
            self.claude = ClaudeClient()  # Now uses Sonnet
            self.s3_client = boto3.client('s3', region_name='us-west-2')
            self.bucket_name = "invoices-bucket-01"
            print("✅ Document processor initialized successfully")
        except Exception as e:
            print(f"❌ Document processor initialization failed: {str(e)}")
            raise

    def process_document(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Enhanced main processing with better error handling and validation."""
        start_time = time.time()
        
        try:
            # Parse the incoming request
            body = self._parse_event_body(event)
            
            # Validate request
            validation_error = self._validate_request(body)
            if validation_error:
                return validation_error
            
            # Route to appropriate processing method
            if 'file_data' in body:
                result = self._process_direct_upload(body)
            elif 's3_key' in body:
                result = self._process_s3_file(body)
            else:
                return self._error_response(400, 'Missing file_data or s3_key in request')
            
            # Add processing time to successful results
            if result.get('statusCode') == 200:
                response_body = json.loads(result['body'])
                response_body['processing_time_seconds'] = round(time.time() - start_time, 2)
                result['body'] = json.dumps(response_body)
            
            return result
            
        except Exception as e:
            print(f"💥 Document processor error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_response(500, f'Processing failed: {str(e)}')

    def _parse_event_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate event body."""
        try:
            body = event.get('body', {})
            if isinstance(body, str):
                body = json.loads(body)
            return body
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in request body: {str(e)}")

    def _validate_request(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate incoming request body."""
        if not body:
            return self._error_response(400, 'Empty request body')
        
        # Check for required fields
        if 'file_data' in body:
            if not body['file_data']:
                return self._error_response(400, 'file_data cannot be empty')
            if not body.get('file_name'):
                return self._error_response(400, 'file_name is required for direct uploads')
        elif 's3_key' in body:
            if not body['s3_key']:
                return self._error_response(400, 's3_key cannot be empty')
        else:
            return self._error_response(400, 'Either file_data or s3_key must be provided')
        
        return None

    def _process_direct_upload(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced direct upload processing with detailed logging."""
        try:
            file_data = body['file_data']
            file_name = body.get('file_name', f'document_{uuid.uuid4().hex}')
            document_type = body.get('document_type', 'invoice')
            
            print(f"🔍 Processing direct upload: {file_name}")
            print(f"📋 Document type: {document_type}")
            
            # Validate and decode file
            try:
                document_bytes = base64.b64decode(file_data)
                print(f"📄 File size: {len(document_bytes)} bytes")
                
                # Basic file validation
                if len(document_bytes) == 0:
                    return self._error_response(400, 'Decoded file is empty')
                if len(document_bytes) > 10 * 1024 * 1024:  # 10MB limit
                    return self._error_response(400, 'File too large (max 10MB)')
                    
            except Exception as decode_error:
                return self._error_response(400, f'Invalid base64 file data: {str(decode_error)}')
            
            # Extract text
            print("📖 Starting text extraction...")
            extraction_result = self.text_extractor.extract_text_from_bytes(document_bytes, file_name)
            
            if 'error' in extraction_result:
                print(f"❌ Text extraction failed: {extraction_result['error']}")
                return self._error_response(422, 'Text extraction failed', extraction_result)
            
            print(f"✅ Text extraction successful - {len(extraction_result.get('raw_text', ''))} characters")
            raw_text = extraction_result['raw_text']
            
            # Validate extracted text
            if not raw_text or len(raw_text.strip()) < 10:
                return self._error_response(422, 'Insufficient text extracted from document')
            
            # Format with Claude
            print("🤖 Starting Claude formatting...")
            structured_data = self._format_with_claude(raw_text, document_type, file_name)
            
            # Validate structured data
            validation_result = self._validate_structured_data(structured_data, raw_text)
            
            # Prepare enhanced response
            result = {
                'success': True,
                'document_name': file_name,
                'document_type': document_type,
                'file_size_bytes': len(document_bytes),
                'extracted_text_length': len(raw_text),
                'extraction_metadata': extraction_result.get('extraction_metadata', {}),
                'extraction_confidence': extraction_result.get('average_confidence', 0),
                'structured_data': structured_data,
                'validation': validation_result,
                'raw_text': raw_text[:1000] + '...' if len(raw_text) > 1000 else raw_text,  # Truncate for response
                'processing_timestamp': time.time(),
                'processing_method': 'direct_upload'
            }
            
            print(f"✅ Processing completed successfully")
            return self._success_response(result)
            
        except Exception as e:
            print(f"💥 Direct upload processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_response(500, f'Direct upload processing failed: {str(e)}')

    def _format_with_claude(self, raw_text: str, document_type: str, file_name: str) -> Dict[str, Any]:
        """Enhanced Claude formatting with retry logic."""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                print(f"🤖 Claude formatting attempt {attempt + 1}/{max_retries + 1}")
                
                # Try Claude formatting
                result = self.claude.format_extracted_text(raw_text, document_type)
                
                # Validate Claude result
                if self._is_valid_claude_result(result):
                    print(f"✅ Claude formatting successful on attempt {attempt + 1}")
                    result['claude_processing'] = True
                    return result
                else:
                    print(f"⚠️ Claude returned incomplete data on attempt {attempt + 1}")
                    if attempt < max_retries:
                        time.sleep(1)  # Brief pause before retry
                        continue
                    
            except Exception as e:
                print(f"⚠️ Claude formatting error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
        
        # All Claude attempts failed, use enhanced fallback
        print(f"🔧 All Claude attempts failed, using enhanced fallback")
        return self._create_enhanced_fallback(raw_text, file_name)

    def _is_valid_claude_result(self, result: Dict[str, Any]) -> bool:
        """Validate Claude result quality."""
        if not isinstance(result, dict) or 'error' in result:
            return False
        
        # Check for essential fields
        essential_fields = ['vendor_name', 'total_amount', 'date']
        found_fields = sum(1 for field in essential_fields if result.get(field) is not None)
        
        # Need at least 2 out of 3 essential fields
        return found_fields >= 2

    def _create_enhanced_fallback(self, raw_text: str, file_name: str) -> Dict[str, Any]:
        """Create enhanced fallback data when Claude fails."""
        print(f"🔧 Creating enhanced fallback structured data")
        
        try:
            # Use the enhanced fallback from Claude client
            result = self.claude._create_enhanced_fallback(raw_text)
            result['claude_processing'] = False
            result['fallback_reason'] = 'Claude formatting failed'
            return result
        except Exception as e:
            print(f"⚠️ Enhanced fallback also failed: {str(e)}")
            # Basic fallback as last resort
            return {
                "vendor_name": None,
                "invoice_number": None,
                "date": None,
                "total_amount": None,
                "currency": "USD",
                "line_items": [],
                "tax_amount": None,
                "payment_terms": None,
                "customer_name": None,
                "confidence_score": 0.1,
                "extraction_method": "basic_fallback",
                "claude_processing": False,
                "fallback_reason": "All extraction methods failed"
            }

    def _validate_structured_data(self, structured_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """Enhanced validation of structured data."""
        validation_result = {
            "is_valid": True,
            "confidence_score": structured_data.get('confidence_score', 0.5),
            "warnings": [],
            "suggestions": [],
            "quality_score": 0.0
        }
        
        # Quality checks
        quality_points = 0
        total_checks = 5
        
        # Check vendor name
        if structured_data.get('vendor_name'):
            quality_points += 1
        else:
            validation_result["warnings"].append("Vendor name not found")
        
        # Check invoice number
        if structured_data.get('invoice_number'):
            quality_points += 1
        else:
            validation_result["warnings"].append("Invoice number not found")
        
        # Check total amount
        total_amount = structured_data.get('total_amount')
        if total_amount and total_amount > 0:
            quality_points += 1
            # Validate amount range
            if total_amount > 1000000:  # Over $1M
                validation_result["warnings"].append(f"Unusually high amount: ${total_amount:,.2f}")
        else:
            validation_result["warnings"].append("Total amount not found or invalid")
        
        # Check date
        if structured_data.get('date'):
            quality_points += 1
        else:
            validation_result["warnings"].append("Invoice date not found")
        
        # Check line items
        line_items = structured_data.get('line_items', [])
        if line_items and len(line_items) > 0:
            quality_points += 1
        else:
            validation_result["warnings"].append("No line items found")
        
        # Calculate quality score
        validation_result["quality_score"] = quality_points / total_checks
        
        # Overall validation
        if quality_points < 2:
            validation_result["is_valid"] = False
            validation_result["suggestions"].append("Manual review required - low extraction quality")
        
        # Try Claude validation if possible
        try:
            claude_validation = self.claude.validate_extraction(structured_data, raw_text[:1000])
            validation_result["claude_validation"] = claude_validation
        except Exception as e:
            print(f"⚠️ Claude validation failed: {str(e)}")
            validation_result["claude_validation"] = {"error": str(e)}
        
        return validation_result

    def _process_s3_file(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced S3 file processing."""
        try:
            s3_key = body['s3_key']
            bucket_name = body.get('bucket_name', self.bucket_name)
            document_type = body.get('document_type', 'invoice')
            
            print(f"📁 Processing S3 file: s3://{bucket_name}/{s3_key}")
            
            # Download file from S3 with enhanced error handling
            try:
                response = self.s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                document_bytes = response['Body'].read()
                file_size = len(document_bytes)
                print(f"📄 Downloaded {file_size} bytes from S3")
                
            except self.s3_client.exceptions.NoSuchKey:
                return self._error_response(404, f'File not found: s3://{bucket_name}/{s3_key}')
            except Exception as s3_error:
                return self._error_response(422, f'S3 download failed: {str(s3_error)}')
            
            # Process the downloaded file
            # Create a temporary body for processing
            temp_body = {
                'file_data': base64.b64encode(document_bytes).decode('utf-8'),
                'file_name': s3_key,
                'document_type': document_type
            }
            
            # Use the same processing logic as direct upload
            result = self._process_direct_upload(temp_body)
            
            # Add S3-specific metadata to successful results
            if result.get('statusCode') == 200:
                response_body = json.loads(result['body'])
                response_body['s3_metadata'] = {
                    'bucket_name': bucket_name,
                    's3_key': s3_key,
                    'file_size_bytes': file_size
                }
                response_body['processing_method'] = 's3_download'
                result['body'] = json.dumps(response_body)
            
            return result
            
        except Exception as e:
            print(f"💥 S3 processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_response(500, f'S3 processing failed: {str(e)}')

    def _success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized success response."""
        return {
            'statusCode': 200,
            'headers': self._get_cors_headers(),
            'body': json.dumps(data, default=str)  # Handle datetime serialization
        }

    def _error_response(self, status_code: int, message: str, details: Any = None) -> Dict[str, Any]:
        """Create standardized error response."""
        error_data = {
            'success': False,
            'error': message,
            'status_code': status_code,
            'timestamp': time.time()
        }
        
        if details:
            error_data['details'] = details
        
        return {
            'statusCode': status_code,
            'headers': self._get_cors_headers(),
            'body': json.dumps(error_data)
        }

    def _get_cors_headers(self) -> Dict[str, str]:
        """Get CORS headers for the response."""
        return {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }

# Global processor instance (for Lambda container reuse)
processor = DocumentProcessor()

def lambda_handler(event, context):
    """
    Enhanced Lambda entry point with better logging and error handling.
    
    Expected event formats:
    
    Direct upload:
    {
        "body": {
            "file_data": "base64_encoded_file_content",
            "file_name": "document.pdf",
            "document_type": "invoice"
        }
    }
    
    S3 file:
    {
        "body": {
            "s3_key": "documents/invoice.pdf",
            "bucket_name": "optional-bucket-name",
            "document_type": "invoice"
        }
    }
    """
    
    print(f"🚀 Lambda handler started")
    print(f"📋 Event keys: {list(event.keys())}")
    
    try:
        result = processor.process_document(event, context)
        print(f"✅ Lambda handler completed with status: {result.get('statusCode')}")
        return result
    except Exception as e:
        print(f"💥 Lambda handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': processor._get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'error': f'Lambda handler error: {str(e)}',
                'timestamp': time.time()
            })
        }