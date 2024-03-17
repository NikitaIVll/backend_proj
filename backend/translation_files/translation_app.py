import os
import time
from backend.translation_files.save_document import save_translated_doc
from backend.model import translator


def translate_text(
        doc_filepath,
        max_tokens,
        models_path,
        model_name,
        lang_orig_code,
        lang_dest_code,
        document_type,
        loaded_model,
):
    if document_type == "docx":
        from backend.translation_files.preprocess_docx import preprocess_text
        from backend.translation_files.translate_docx import translate_document
    elif document_type in ["pdf", "PDF"]:
        from backend.translation_files.preprocess_pdf import preprocess_text
        from backend.translation_files.translate_pdf import translate_document
    elif document_type == "pptx":
        from backend.translation_files.preprocess_pptx import preprocess_text
        from backend.translation_files.translate_pptx import translate_document
    else:
        raise ValueError("Unsupported file type")
    language, document = preprocess_text(
        doc_filepath=doc_filepath, language=lang_orig_code
    )
    translated_document = translate_document(
        document=document,
        model_name=model_name,
        models_path=models_path,
        max_tokens=max_tokens,
        lang_origin_code=language,
        lang_dest_code=lang_dest_code,
        loaded_model=loaded_model,
    )
    return translated_document


def translate_document(filename, dst_lang, loaded_model=None):
    doc_name = filename
    model_name = "nllb-200-distilled-600M"
    scr_lang = None
    max_tokens = 150
    filepath = os.path.abspath(__file__)
    projpath = os.path.abspath(os.path.join(filepath, ".."))
    models_path = os.path.join(projpath, "models")
    input_path = os.path.join(projpath, "test", "in")
    doc_filepath = os.path.join(input_path, doc_name)
    output_path = os.path.join(projpath, "test", "out")
    output_filename = f"translated_{doc_name}"
    output_file = os.path.join(output_path, output_filename)
    doc_type = doc_name.split(".")[-1]
    start = time.time()
    translated_document = translate_text(
        doc_filepath=doc_filepath,
        max_tokens=max_tokens,
        models_path=models_path,
        model_name=model_name,
        lang_orig_code=scr_lang,
        lang_dest_code=dst_lang,
        document_type=doc_type,
        loaded_model=loaded_model,
    )
    save_translated_doc(translated_document, output_file, doc_type)
    if os.path.exists(input_path):
        for file in os.listdir(input_path):
            os.remove(os.path.join(input_path, file))
        os.rmdir(input_path)
    os.makedirs(input_path)
    end = time.time()
    print(f"Total time:{end - start} s")
