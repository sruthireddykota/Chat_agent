from pydantic import BaseModel, Field

from uuid import uuid4
from datetime import datetime, timezone

from app.models.constants import WorkflowType, Status

def _id():
    return str(uuid4())

def _time_now():
    return datetime.now(timezone.utc).isoformat()
    

class WorkflowStep(BaseModel):

    id : str = Field(default_factory = _id)
    name : str = Field(description="Step name")
    instructions : str = Field(description="Step Instructions")
    created_timestamp : str = Field(default_factory=_time_now)
    updated_timestamp : str = Field(default_factory=_time_now)

    def touch(self):
        self.updated_timestamp = _time_now()

class WorkflowBuilder(BaseModel):

    id : str = Field(default_factory=_id)
    creator_id : str = Field(description="Workflow Creator")
    name: str = Field(description="Workflow Name")
    description: str = Field(description="description of the workflow")
    workflow_type : WorkflowType = Field(description="Workflow type",
                                         default = WorkflowType.CONCURRENT)
    steps : list[WorkflowStep] = Field(default_factory=list)
    created_timestamp : str = Field(default_factory=_time_now)
    updated_timestamp : str = Field(default_factory=_time_now)

    def touch(self):
            self.updated_timestamp = _time_now()

class StepResult(BaseModel):

    id : str = Field(default_factory=_id)
    name : str = Field(description="Step name")
    response : str = Field(description="response")
    status : Status = Field(default = Status.NOTSTARTED)

class WorkflowResult(BaseModel):

    id : str = Field(default_factory=_id)
    name : str = Field(description="Workflow name")
    run_start : str = Field(default_factory = _time_now)
    run_end : str = Field(default_factory = _time_now)
    duration : float = 0.0
    response : list[StepResult] = Field(default_factory=list)
    combined_response: str = Field(description="Combined response")
    status : Status = Field(default= Status.NOTSTARTED)

    def touch(self):
        self.run_end = _time_now()
        start = datetime.fromisoformat(self.run_start)
        end = datetime.fromisoformat(self.run_end)

        self.duration = (end - start).total_seconds()
