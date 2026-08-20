from datetime import datetime, timezone
from app.models.workflow import WorkflowBuilder
from app.utils.logger import get_logger

from app.models.constants import Status
from app.models.workflow import StepResult, WorkflowResult, WorkflowBuilder

from app.workflows.workflow_builder import WorkflowBuilderr


logger = get_logger()


class WorkflowExecutor:

    async def invoke_workflow(self,workflow):
        try :

            result={}
            run_start= datetime.now(timezone.utc).isoformat()
            step_outputs = await self.run_workflow(workflow=workflow)
            combined_response = ""

            if step_outputs:
                combined_response = await self.aggregator(step_outputs=step_outputs)

            result["name"] = workflow.name
            result["response"] = step_outputs
            result["combined_response"]= combined_response
            result["status"] = Status.SUCCESS
            result["run_start"] = run_start

            result = WorkflowResult(**result)
            result.touch()

            return result

        except Exception as e:
            logger.error("Workflow execution failed {e}")

    async def run_workflow(self, workflow: WorkflowBuilder):   
            try:
                step_names = [step.name for step in workflow.steps]
                build = WorkflowBuilderr()

                built_workflow = await build.build_workflow(
                    workflow=workflow
                )
                events = await built_workflow.run("")

                step_outputs = []

                for event in events:
                    step_output = {}
                    if event.type != "executor_completed":
                        continue
                    # Ignores final aggregator
                    if event.executor_id == "aggregator":
                        continue
                    if event.executor_id not in step_names:
                        continue

                    executor_result = event.data[0]
                    agent_response = executor_result.agent_response
                    response_text = ""

                    for msg in agent_response.messages:
                        if msg.text:
                            response_text += msg.text

                    step_output["name"] = event.executor_id
                    step_output["response"] = response_text
                    step_output["status"] = Status.SUCCESS

                    step_output= StepResult(**step_output)
                    step_outputs.append(step_output)

                return step_outputs

            except Exception as e:
                logger.error(f"[Workflow] failed : {e}")

    async def aggregator(self, step_outputs):

        try :
            combined_response = ""
            for step in step_outputs:

                combined_response +=(
                    f"\n{'-' * 60}\n"
                    f"[- {step.name}]\n"
                    f"{step.response}\n"
            )
            return combined_response

        except Exception as e:
            logger.error(f"[Workflow Aggregator]: Failed {e}")
            return ""
