import os

from typing import Union, Literal


def srt_file_to_txt_file(path: str):
    regex = r"[\d:,]+ --> [\d:,]+"
    pass


def get_prefix_env_name(var_prefix: str):
    return any([env_var.startswith(var_prefix) for env_var in os.environ])


def get_env_name() -> Union[
    Literal["Kaggle"],
    Literal["JupyterServer"],
    Literal["Colab"],
    Literal["VSCode"],
    None,
]:
    if get_prefix_env_name("KAGGLE_"):
        return "Kaggle"
    if get_prefix_env_name("JPY_"):
        return "JupyterServer"

    if get_prefix_env_name("COLAB_"):
        return "Colab"

    if get_prefix_env_name("VSCODE_"):
        return "VSCode"
    return None
