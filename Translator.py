from google_trans_new import google_translator  

def Translator(text, language):  
    translator = google_translator()  
    translate_text = translator.translate(text, lang_src='en', lang_tgt=language)  
    return translate_text