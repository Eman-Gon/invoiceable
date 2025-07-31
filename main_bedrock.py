from textract_handler_enhanced import extract_with_textract
from bedrock_invoice_extractor import invoke_bedrock

bucket = "csu-summer-camp-invoice-extraction-2025"
docs = [
    "Data/CalPoly_MayBilling_05312025.pdf",
    "Data/Invoice_6792_2025-06-30.pdf"
]

for doc in docs:
    print(f"\n--- Extracted text from {doc} ---\n")
    raw_text = extract_with_textract(bucket, doc)
    print(raw_text)

    print(f"\n--- LLM output for {doc} ---\n")
    prompt = f"Extract the following invoice into JSON format with keys: invoice_number, date, bill_to, amount_due, line_items, and due_date. Respond with just the JSON.\n\n{raw_text}"
    structured_output = invoke_bedrock(prompt)
    print(structured_output)

