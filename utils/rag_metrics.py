import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timezone
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric
)
from deepeval.test_case import LLMTestCase
from config.settings import settings

def get_mongo_collection():
    mongo_client = MongoClient(settings.MONGODB_URI)
    mongo_db     = mongo_client[settings.MONGODB_DB]
    return mongo_db[settings.MONGODB_COLLECTION]


def evaluate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates a DataFrame with columns [Questions, Response, Context].
    Scores are computed via DeepEval and written to MongoDB.
    """

    from deepeval.models import AzureOpenAIModel

    model = AzureOpenAIModel(
        model=settings.AZURE_DEPLOYMENT_NAME,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.OPENAI_API_VERSION
    )

    #metrics
    answer_relevance  = AnswerRelevancyMetric(threshold=0.5, model=model)
    context_relevance = ContextualRelevancyMetric(threshold=0.5, model=model)
    faithfulness      = FaithfulnessMetric(threshold=0.5, model=model)  # = groundedness

    results_col = get_mongo_collection()
    score_rows  = []

    for _, row in df.iterrows():
        query   = str(row["Questions"])
        answer  = str(row["Response"])
        context = row["Context"]

        if isinstance(context, str):
            context = [context]
        elif not isinstance(context, list):
            context = [str(context)]

        test_case = LLMTestCase(
            input=query,
            actual_output=answer,
            retrieval_context=context
        )

        answer_relevance.measure(test_case)
        context_relevance.measure(test_case)
        faithfulness.measure(test_case)

        scores = {
            "Answer Relevance":  answer_relevance.score,
            "Context Relevance": context_relevance.score,
            "Groundedness":      faithfulness.score
        }

        #to MongoDB
        mongo_doc = {
            "query":             query,
            "answer":            answer,
            "context":           context,
            "answer_relevance":  scores["Answer Relevance"],
            "context_relevance": scores["Context Relevance"],
            "groundedness":      scores["Groundedness"],
            "evaluated_at":      datetime.now(timezone.utc).isoformat()
        }
        results_col.insert_one(mongo_doc)
        score_rows.append(scores)

    scores_df = pd.DataFrame(score_rows)
    result_df = pd.concat([df.reset_index(drop=True), scores_df], axis=1)
    return result_df