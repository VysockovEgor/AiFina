from spacy.lang.ru import Russian


def No_Punc(txt):
    nlp = Russian()
    doc = nlp(txt)
    txt_new = ""
    for token in doc:
        if token.text =='\n':
            txt_new += token.text
            continue
        if not token.is_alpha and not token.like_num:
            continue
        if not token.is_punct:
            txt_new += token.text + " "
    return txt_new




