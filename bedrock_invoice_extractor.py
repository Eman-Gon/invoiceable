import boto3
import json

def invoke_bedrock(prompt):
    session = boto3.Session(profile_name="cpisb_IsbUsersPS-962448382783")
    bedrock = session.client("bedrock-runtime", region_name="us-west-2")
    
    # ✅ UPDATED: Use the confirmed working model ID
    model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"  # This one works!
    
    # Use the correct payload format for Anthropic models on Bedrock
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,  # Increased for invoice extraction
        "temperature": 0.1   # Lower for more consistent structured output
    }
    
    try:
        response = bedrock.invoke_model(
            modelId=model_id,  # ✅ Use the variable instead of hardcoded
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )
        
        result = json.loads(response['body'].read().decode())
        return result['content'][0]['text']
        
    except Exception as e:
        print(f"Error invoking Bedrock: {e}")
        return None


def extract_invoice_data(textract_output):
    """
    Enhanced function specifically for invoice extraction
    """
    prompt = f"""Extract structured data from this invoice OCR output. Return ONLY a valid JSON object with these fields:

Required fields:
- vendor_name: Company/person who sent the invoice
- invoice_number: Invoice or reference number  
- invoice_date: Date of invoice (YYYY-MM-DD format)
- due_date: Payment due date (YYYY-MM-DD format if available)
- total_amount: Total amount due (number only, no currency symbols)
- currency: Currency code (USD, EUR, etc.)
- line_items: Array of items with description, quantity, unit_price, total

Optional fields:
- vendor_address: Full address of vendor
- customer_name: Who the invoice is billed to
- customer_address: Billing address
- payment_terms: Payment terms if specified
- tax_amount: Tax amount if separated
- subtotal: Subtotal before tax

OCR Output:
{textract_output}

Return only valid JSON, no additional text or explanations."""

    return invoke_bedrock(prompt)


# Test function to verify the fix works
def test_bedrock_connection():
    """Quick test to verify Bedrock connection works with new model"""
    test_response = invoke_bedrock("Say 'Invoice extraction is ready!' in JSON format")
    print("Test response:", test_response)
    return test_response


if __name__ == "__main__":
    # Quick test
    print("Testing Bedrock connection...")
    test_bedrock_connection()