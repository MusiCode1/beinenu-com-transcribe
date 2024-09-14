import re


def remove_hebrew_niqqud(text: str):

    niqqud_pattern = re.compile(r"[\u0591-\u05C7]")

    clean_text = re.sub(niqqud_pattern, "", text)

    return clean_text


def remove_pesukim_letters(text: str):

    psukim_pattern = re.compile(r"(^|(\.)\s\s|\n)[א-ת]{1,2}\s")

    def replacement(match):
        if match.group(2):
            return match.group(2) + "\r\n"
        return "\r\n" 
    
    clean_text = re.sub(psukim_pattern, replacement, text)

    return clean_text


def remove_curly_braces_and_content(text: str):

    pattern = re.compile(r"\{.*?\}")

    return re.sub(pattern, "", text)


def remove_extra_spaces(text: str):
    
    pattern = re.compile(r" {2,}")

    return re.sub(pattern, " ", text)


def replace_colon_and_semicolon_with_comma(text: str):

    return text.replace(':', ',').replace(';', ',').replace("--", " ")


def remove_extra_characters(text: str, chars:str):
    return text.replace(chars, '')


def remove_extra_new_lines(text: str):
    text = text.replace("\r\n", "\n")
    
    pattern = re.compile(r"(\r\n{2,})|(\n{2,})")
    
    text = re.sub(pattern, "\n", text)
    
    return text


def clean_the_text(text):
    clean_text = remove_pesukim_letters(text)
    clean_text = replace_colon_and_semicolon_with_comma(clean_text)
    clean_text = remove_curly_braces_and_content(clean_text)
    clean_text = remove_hebrew_niqqud(clean_text)
    clean_text = remove_extra_spaces(clean_text)
    clean_text = remove_extra_new_lines(clean_text)
    
    return clean_text.strip()

