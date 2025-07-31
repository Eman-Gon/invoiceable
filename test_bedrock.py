from textract_handler_enhanced import extract_with_textract
from bedrock_invoice_extractor import invoke_bedrock

def test_invoice_pipeline():
    bucket = "csu-summer-camp-invoice-extraction-2025"
    doc = "Data/TestInvoice.pdf"

    textract_data = extract_with_textract(bucket, doc)

    text = "\n".join(
        block["Text"] for block in textract_data.get("Blocks", []) if block["BlockType"] == "LINE"
    )

    llm_result = invoke_bedrock(f"Summarize this invoice:\n\n{text}")
    print(llm_result)

if __name__ == "__main__":
    test_invoice_pipeline()
