import re


def remove_hebrew_niqqud(text: str):

    niqqud_pattern = re.compile(r"[\u0591-\u05C7]")

    clean_text = re.sub(niqqud_pattern, "", text)

    return clean_text


def remove_pesukim_letters(text: str):

    psukim_pattern = re.compile(r"(^|\.\s|\s\s)[א-ת]{1,2}\s")

    clean_text = re.sub(psukim_pattern, "\r\n", text)

    return clean_text


def remove_curly_braces_and_content(text: str):

    pattern = re.compile(r"\{.*?\}")

    return re.sub(pattern, "", text)

def remove_extra_spaces(text: str):

    return ' '.join(text.split())

def replace_colon_and_semicolon_with_comma(text: str):

    return text.replace(':', ',').replace(';', ',')

def remove_extra_characters(text: str, chars:str):
    return text.replace(chars, '')

def clean_the_text(text):
    clean_text = remove_pesukim_letters(text)
    clean_text = replace_colon_and_semicolon_with_comma(clean_text)
    clean_text = remove_curly_braces_and_content(clean_text)
    clean_text = remove_hebrew_niqqud(clean_text)
    clean_text = remove_extra_spaces(clean_text)
    clean_text = clean_text.replace("--", " ")
    return clean_text
