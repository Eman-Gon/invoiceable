# api_server.py - API that uploads to S3 then processes
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import json
import boto3
import uuid
from textract_handler_enhanced import extract_with_textract  # Your S3-based function
from bedrock_invoice_extractor import extract_invoice_data   # Your existing function

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# S3 configuration
S3_BUCKET = "csu-summer-camp-invoice-extraction-2025"  # Your actual bucket
S3_PREFIX = "invoices/"  # Optional: organize files in a folder

def upload_to_s3_and_process(file_path, filename):
    """
    Upload file to S3 and process with your existing S3-based pipeline
    """
    session = boto3.Session(profile_name="cpisb_IsbUsersPS-962448382783")
    s3_client = session.client("s3", region_name="us-west-2")
    
    # Generate unique filename to avoid conflicts
    s3_key = f"{S3_PREFIX}{uuid.uuid4()}_{filename}"
    
    try:
        # Upload to S3
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        
        # Process with your existing S3-based Textract function
        textract_output = extract_with_textract(S3_BUCKET, s3_key)
        
        # Clean up S3 file (optional)
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        
        return textract_output
        
    except Exception as e:
        # Clean up S3 file if it exists
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except:
            pass
        raise e

@app.route('/api/extract-invoice', methods=['POST'])
def extract_invoice():
    """
    Single endpoint for frontend to send PDF files
    
    Expected: multipart/form-data with 'file' field containing PDF
    Returns: JSON with extracted invoice data
    """
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file selected'
            }), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False, 
                'error': 'Only PDF files are supported'
            }), 400
        
        # Process the file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            
            try:
                # Your existing pipeline
                print(f"Processing: {file.filename}")
                
                # Step 1: Upload to S3 and process with Textract
                textract_output = upload_to_s3_and_process(temp_file.name, file.filename)
                if not textract_output:
                    return jsonify({
                        'success': False,
                        'error': 'Could not extract text from PDF'
                    }), 500
                
                # Step 2: Claude extraction
                extracted_data = extract_invoice_data(textract_output)
                if not extracted_data:
                    return jsonify({
                        'success': False,
                        'error': 'Could not extract invoice data'
                    }), 500
                
                # Parse JSON if it's a string
                if isinstance(extracted_data, str):
                    try:
                        extracted_data = json.loads(extracted_data)
                    except json.JSONDecodeError:
                        # Return raw text if JSON parsing fails
                        extracted_data = {'raw_response': extracted_data}
                
                # Success response
                return jsonify({
                    'success': True,
                    'filename': file.filename,
                    'data': extracted_data
                })
                
            finally:
                # Clean up temp file
                os.unlink(temp_file.name)
                
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check for frontend to verify API is running"""
    return jsonify({
        'status': 'healthy',
        'service': 'invoice-extractor-api'
    })

@app.route('/api/batch-extract', methods=['POST'])
def batch_extract():
    """
    Optional: Handle multiple files at once
    Expected: multipart/form-data with multiple 'files' fields
    """
    try:
        files = request.files.getlist('files')
        results = []
        
        for file in files:
            if file.filename.lower().endswith('.pdf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    file.save(temp_file.name)
                    
                    try:
                        textract_output = upload_to_s3_and_process(temp_file.name, file.filename)
                        extracted_data = extract_invoice_data(textract_output)
                        
                        if isinstance(extracted_data, str):
                            extracted_data = json.loads(extracted_data)
                        
                        results.append({
                            'filename': file.filename,
                            'success': True,
                            'data': extracted_data
                        })
                        
                    except Exception as e:
                        results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': str(e)
                        })
                    finally:
                        os.unlink(temp_file.name)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Invoice Extractor API Started")
    print("📡 Endpoint: POST http://localhost:5001/api/extract-invoice")
    print("🔍 Health Check: GET http://localhost:5001/api/health")
    app.run(debug=True, host='0.0.0.0', port=5001)