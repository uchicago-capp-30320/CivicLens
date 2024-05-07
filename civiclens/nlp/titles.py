import polars as pl
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from ..utils.database_access import pull_data


def get_doc_summary(id: str) -> pl.DataFrame:
    query = f"""
            SELECT id, summary
            FROM regulations_document
            WHERE id = '{id}'
            """
    schema = ["id", "summary"]
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
