from . import app_logger
import ctranslate2
import transformers
from nltk.tokenize import sent_tokenize
import os
import re


def split_into_paragraphs(text):
    paragraphs = re.split(r'(\n+)', text)
    paragraphs = [p.replace('\n', '<br>') for p in paragraphs]
    return paragraphs


class Translator():
    def __init__(self, models_dir, model):
        self.models_dir = models_dir
        self.logger = app_logger.get_logger("translator")
        self.models = {}
        self.model = model
        # self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = 'cpu'
        self.path = os.path.join(models_dir, self.model)
        success_code, message = self.load_model_nllb()
        self.logger.info("result of load model: %s", message)
        print(success_code, message)

    def load_model_nllb(self):
        self.logger.info("load model - %s, path - %s, device - %s", self.model, self.path, self.device)
        try:
            model = ctranslate2.Translator(self.path, device=self.device)
            self.logger.info("model loaded")
        except FileNotFoundError:
            self.logger.error("Make sure you have downloaded NLLB model for translation")
            return 0, f"Make sure you have downloaded NLLB model for translation"
        except Exception as e:
            self.logger.error("An error occurred while loading the model: %s", str(e))
            return 0, f"An error occurred while loading the model: {str(e)}"
        self.models['nllb'] = (model, None)
        return 1, f"Successfully loaded NLLB model for translation"

    def translate_text(self, source, target, text):
        self.logger.info("translation from %s to %s", source, target)
        paragraphs = split_into_paragraphs(text)
        translated_paragraphs = []
        translator = self.models['nllb'][0]
        tokenizer = transformers.AutoTokenizer.from_pretrained(os.path.join(self.models_dir, 'tokenizers', self.model),
                                                               src_lang=source, device=self.device)
        for paragraph in paragraphs:
            sentences = sent_tokenize(paragraph)
            if "<br>" in paragraph:
                translated_paragraphs.append(paragraph)
                continue
            translated_sentences = []
            target_prefix = [target]
            for sentence in sentences:
                source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(sentence))
                try:
                    results = translator.translate_batch([source_tokens], target_prefix=[target_prefix])
                    target_tokens = results[0].hypotheses[0][1:]
                    translated_sentences.append(
                        tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens), skip_special_tokens=True))
                except Exception as e:
                    self.logger.error("An error occurred during translation: %s", str(e))
                    return "An error occurred during translation"
            translated_paragraphs.append(' '.join(translated_sentences))
        translated_text = ''.join(translated_paragraphs)
        return translated_text.replace('<br>', '\n')

    def translate_file(self, src_lang, tgt_lang, text):
        translator = ctranslate2.Translator("nllb-200-distilled-600M")
        tokenizer = transformers.AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", src_lang=src_lang)

        source = tokenizer.convert_ids_to_tokens(tokenizer.encode("Hello world!"))
        target_prefix = [tgt_lang]
        results = translator.translate_batch([source], target_prefix=[target_prefix])
        target = results[0].hypotheses[0][1:]

        print(tokenizer.decode(tokenizer.convert_tokens_to_ids(target)))