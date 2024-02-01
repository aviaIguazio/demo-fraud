# Copyright 2024 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import mlrun

def setup(
        project: mlrun.projects.MlrunProject
) -> mlrun.projects.MlrunProject:
    """
    Creating the project for this demo. This function is expected to be called automatically when
    calling the function `mlrun.get_or_create_project`.

    :returns: a fully prepared project for this demo.
    """
    # Set the project git source:
    source = project.get_param(key="source")
    if source:
        print(f"Project Source: {source}")
        project.set_source(source=source, pull_at_runtime=True)

    if project.get_param("pre_load_data"):
        print("pre_load_data")

    # Refresh MLRun hub to the most up-to-date version:
    mlrun.get_run_db().get_hub_catalog(source_name="default", force_refresh=True)


    # Set the functions:
    _set_function(
        project=project,
        func = "hub://get_offline_features",
        name="get-vector",
        kind="job",
    )

    _set_function(
        project=project,
        func="hub://feature_selection",
        name="feature-selection",
        kind="job",
    )

    _set_function(
        project=project,
        func="hub://auto_trainer",
        name="train",
        kind="job",
    )
    _set_function(
        project=project,
        func="hub://auto_trainer",
        name="evaluate",
        kind="job",
    )

    _set_function(
        project=project,
        func="hub://v2_model_server",
        name="serving",
        kind="job",
    )

    # Set the training workflow:
    project.set_workflow("main", "src/train_workflow.py")

    # Save and return the project:
    project.save()
    return project


def _set_function(
        project: mlrun.projects.MlrunProject,
        func: str,
        name: str,
        kind: str,
        gpus: int = 0,
        node_name: str = None,
        image: str = None,
):
    # Set the given function:
    with_repo = not func.startswith("hub://")
    mlrun_function = project.set_function(
        func=func, name=name, kind=kind, with_repo=with_repo, image=image,
    )

    # Configure GPUs according to the given kind:
    if gpus >= 1:
        mlrun_function.with_node_selection(node_selector={"app.iguazio.com/node-group": "added-t4"})
        if kind == "mpijob":
            # 1 GPU for each rank:
            mlrun_function.with_limits(gpus=1)
            mlrun_function.spec.replicas = gpus
        else:
            # All GPUs for the single job:
            mlrun_function.with_limits(gpus=gpus)
    # Set the node selection:
    elif node_name:
        mlrun_function.with_node_selection(node_name=node_name)
    # Save:
    mlrun_function.save()
