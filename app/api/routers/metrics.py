from fastapi import APIRouter, status, HTTPException, UploadFile, File
from pymongo.errors import PyMongoError
from io import BytesIO
from uuid import uuid4
import pandas as pd

from app.repositeries.mongodb_server import MongoStore
from app.agents.rag.rag_agent import RAGAgent
from app.utils.rag_metrics import evaluate_dataframe

mongo=MongoStore()
router= APIRouter(prefix="/api/v1",tags=["Metrics"])


@router.get("/metrics/averages")
def get_average_metrics():
    try:
        metrics=mongo.get_average_metrics()
        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate metrics"
            )

        return metrics

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/metrics/evaluate")
async def evaluate_rag_file(file: UploadFile = File(...)):
    """Generate RAG answers for a CSV of questions and evaluate them."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file")

    try:
        dataframe = pd.read_csv(BytesIO(await file.read()))
        question_column = next(
            (column for column in ("Questions", "question", "Question") if column in dataframe.columns),
            None,
        )
        if question_column is None:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain a Questions, question, or Question column",
            )

        questions = dataframe[question_column].dropna().astype(str).tolist()
        if not questions:
            raise HTTPException(status_code=400, detail="CSV contains no questions")

        session_id = f"evaluation-{uuid4().hex[:12]}"
        mongo.create_session(session_id, "evaluation-user")
        rag = RAGAgent(session_id=session_id)
        responses = []
        contexts = []
        for question in questions:
            result = await rag.invoke_agent({
                "session_id": session_id,
                "query": {"text": question, "files": []},
                "user_id": "evaluation-user",
            })
            result = result or {}
            responses.append(result.get("response", ""))
            contexts.append(result.get("context", []))

        evaluation_frame = pd.DataFrame({
            "Questions": questions,
            "Response": responses,
            "Context": contexts,
        })
        scored = evaluate_dataframe(evaluation_frame)
        score_columns = ["Answer Relevance", "Context Relevance", "Groundedness"]
        averages = {
            column: float(scored[column].mean())
            for column in score_columns
            if column in scored.columns
        }
        return {
            "filename": file.filename,
            "count": len(questions),
            "averages": averages,
            "results": scored.fillna("").to_dict(orient="records"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
