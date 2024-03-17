from backend.translation_files.translation_app import translate_document


model_name = "nllb-200-3.3B"
max_tokens = 150
# model = load_model(f"facebook/{model_name}")

translate_document("data/sample.pdf", "rus_Cyrl")























# import requests
# from docx import Document
#
#
# def translate_text(text, api_url, source_language, target_language):
#     try:
#         response = requests.post(api_url, json={"text": text, "source": source_language, "target": target_language})
#         response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
#         return response.json()["translated"]
#     except requests.RequestException as e:
#         print(f"Translation request failed: {e}")
#         return None
#
#
# def translate_docx(input_file, output_file, source_language, target_language):
#     document = Document(input_file)
#     new_document = Document()
#     url = "http://127.0.0.1:7060/translate"
#     for paragraph in document.paragraphs:
#         translated_text = translate_text(paragraph, url,  source_language, target_language)
#         new_paragraph = new_document.add_paragraph(translated_text)
#         new_paragraph.style = paragraph.style
#
#     new_document.save(output_file)
#
# # Usage:
# translate_docx("./data/sample.docx", "./output/sample.docx", "eng_Latn", "rus_Cyrl")
