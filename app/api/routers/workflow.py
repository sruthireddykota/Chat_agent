from fastapi import APIRouter, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pymongo.errors import PyMongoError
from pydantic import ValidationError

from app.api.auth import current_user
from app.models.workflow import WorkflowBuilder

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])



def _parse_workflow(payload: dict, creator_id: str, workflow_id: str | None = None):
    data = dict(payload)
    data["creator_id"] = creator_id
    if workflow_id is not None:
        data["id"] = workflow_id
    try:
        return WorkflowBuilder.model_validate(data)
    
    except ValidationError as e:
        raise HTTPException(status_code=422, 
                            detail=f"Error{e}") 

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, req: Request):

    user = current_user(req)
    try:
        mongo = req.app.state.mongo_store
        if not await mongo.delete_workflow(workflow_id, user["sub"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="Workflow not found")
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e)) from e


@router.get("/{workflow_id}", status_code=status.HTTP_200_OK)
async def get_workflow(workflow_id: str, req: Request):
    user = current_user(req)
    mongo = req.app.state.mongo_store
    try:
        workflow = await mongo.get_workflow(workflow_id, user["sub"])
        if workflow is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="Workflow not found")
        
        return jsonable_encoder(workflow)
    
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e))


@router.get("", status_code=status.HTTP_200_OK)
async def list_workflows(req: Request):
    user = current_user(req)
    mongo=req.app.state.mongo_store
    try:

        workflows = await mongo.get_workflows(user["sub"])
        if workflows is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Failed to retrieve workflows")
        return jsonable_encoder(workflows)
    
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e)
                            )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: dict, req: Request):
    user = current_user(req)
    mongo = req.app.state.mongo_store
    try:
        workflow = _parse_workflow(payload, user["sub"])
        workflow_id = await mongo.save_workflow(workflow)

        if workflow_id is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Failed to save workflow")
        return jsonable_encoder(workflow)
    
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"MongoDB Error: {e}"
                            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e)) 


@router.put("/{workflow_id}", status_code=status.HTTP_200_OK)
async def update_workflow(workflow_id: str, payload: dict, req: Request):
    user = current_user(req)
    try:
        existing = await req.app.state.mongo_store.get_workflow(workflow_id, user["sub"])

        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="Workflow not found")
        
        workflow = _parse_workflow(payload, user["sub"], workflow_id)
        workflow = workflow.model_copy(update={"created_timestamp": existing["created_timestamp"]})
        workflow.touch()

        if not await req.app.state.mongo_store.update_workflow(workflow, user["sub"]):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="Failed to update workflow")
        
        return jsonable_encoder(workflow)
    except PyMongoError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail=f"MongoDB Error: {e}"
                                )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e)) from e