import pymupdf
import fitz 

def extract_text_from_pdf(path: str) -> str:
    """
      Extracts text content from all pages of a PDF file.

      Parameters:
          path (str): The file path to the PDF document.

      Returns:
          str: The extracted text from the entire PDF.
    """
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text


path_to_pdf = "../nos-gen-ai-hackathon/raw_data/document_to_anonymize.pdf"
extracted_text = extract_text_from_pdf(path_to_pdf)
print(extracted_text)

txt_path = path_to_pdf.replace(".pdf", ".txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(extracted_text)

print(f"✅ Text extracted and saved to: {txt_path}")