import polars as pl
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from ..utils.database_access import pull_data


def get_doc_summaries() -> pl.DataFrame:
    query = """
        SELECT id, last_modified_date, title, summary
        FROM regulations_document
        ORDER BY last_modified_date DESC
        LIMIT 100;
        """
    schema = ["id", "last_modified_date", "title", "summary"]
    return pull_data(query, schema)


class TitleChain:
    """Creates more accessible titles for regulation documnents"""

    def __init__(self) -> None:
        self.template = """You are a title generator that is given a paragraph
        summary of a regulation. You job is to create a title that conveys the
        content of the paragraph summary in a succinct way that highlights the
        content that would be relevant to someone who is civically engaged and
        looking to find interesting regulations to comment on.

            Regulation Summary: {paragraph}

            Answer:"""
        self.prompt = PromptTemplate.from_template(self.template)
        self.hf_pipeline = HuggingFacePipeline.from_model_id(
            model_id="google/flan-t5-base",
            task="text2text-generation",
            pipeline_kwargs={"max_length": 20},
        )
        self.parse = StrOutputParser()
        self.chain = self.prompt | self.hf_pipeline | self.parse

    def invoke(self, paragraph: str) -> str:
        return self.chain.invoke({"paragraph": paragraph})


# rough code for running this on a set of documents, will adjust
df = get_doc_summaries()
title_creator = TitleChain()
titles = {"original_titles": [], "new_titles": []}
for row in df.iter_rows():
    if row[3] is not None:
        titles["original_titles"].append(row[2])
        titles["new_titles"].append(title_creator.invoke(paragraph=row[3]))

df = pl.from_dict(titles)
