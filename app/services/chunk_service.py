from langchain.text_splitter import (
    RecursiveCharacterTextSplitter
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)


def split_text(text: str):

    return splitter.split_text(text)