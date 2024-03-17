from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
from tqdm import tqdm
from backend.translation_files.utils import convert_text, basic_preprocessing
import torch
import ctranslate2


def translate_document(document, model_name, models_path, max_tokens, lang_origin_code, lang_dest_code, loaded_model):
    translator = docx_translator(model_name, models_path, max_tokens, lang_origin_code, lang_dest_code, loaded_model)
    translator.translate_document(document)
    return document


class docx_translator:
    def __init__(
            self,
            model_name,
            models_path,
            max_tokens,
            lang_origin_code,
            lang_dest_code,
            loaded_model,
    ):
        # self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = 'cpu'
        self.model = None
        self.tokenizer = AutoTokenizer.from_pretrained(
            os.path.join("facebook/", model_name), src_lang=lang_origin_code
        )
        if loaded_model:
            self.model = loaded_model
        else:
            tok = None
            try:
                self.model = ctranslate2.Translator("/opt/models/nllb-200-600M", device=self.device)
            except:
                print(f"Make sure you have downloaded NLLB model for translation")
        self.max_tokens = max_tokens
        self.lang_dest_code = lang_dest_code

    def translate_document(self, document):
        self.body_content(document)
        self.body_tables(document)
        self.headers(document)
        self.footers(document)

    def body_content(self, document):
        print("\tProcessing paragraphs...")
        for paragraph in tqdm(document.paragraphs):
            self.Execute(paragraph)

    def body_tables(self, document):
        print("\tProcessing body tables...")
        for table in tqdm(document.tables):
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self.Execute(paragraph)

    def headers(self, document):
        print("\tProcessing headers ...")
        for section in tqdm(document.sections):
            for paragraph in section.header.paragraphs:
                self.Execute(paragraph)
            for table in section.header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            self.Execute(paragraph)

    def footers(self, document):
        print("\tProcessing footers ...")
        for section in document.sections:
            for paragraph in section.footer.paragraphs:
                self.Execute(paragraph)
            for table in section.footer.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            self.Execute(paragraph)

    def Execute(self, paragraph):
        translator = self.model
        for run in paragraph.runs:
            original_text = run.text
            case1 = original_text == ""
            case2 = sum([letter.isalpha() for letter in original_text]) <= 3
            cases = case1 or case2
            if not cases:
                text_chunks = convert_text(
                    original_text, self.tokenizer, self.max_tokens
                )
                translated_text = []
                for text_chunk in text_chunks:
                    source_tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text_chunk))
                    target_prefix = [self.lang_dest_code]
                    results = translator.translate_batch([source_tokens], target_prefix=[target_prefix])
                    target = results[0].hypotheses[0][1:]
                    translated_text.append(self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(target)))
                translated_text = " ".join(translated_text)
                run.text = translated_text
