from textract_handler import extract_text_from_pdf

result = extract_text_from_pdf(
    "csu-summer-camp-invoice-extraction-2025",
    "Data/CalPoly_MayBilling_05312025.pdf"
)
print(result)
