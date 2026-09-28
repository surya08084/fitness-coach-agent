# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_exercise,
    calculate_workout_metrics,
    fetch_food_nutrition_info,
    find_nearby_places,
    generate_domain_image,
    generate_domain_video,
    generate_fitness_image,
    geocode_address,
    get_exercise_details,
    list_exercises,
)


def _load_agent_engine_resource_name() -> str | None:
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r") as f:
                data = json.load(f)
                return data.get("remote_agent_runtime_id")
        except Exception:
            pass
    return None


agent_engine_name = _load_agent_engine_resource_name()
if agent_engine_name and "GOOGLE_CLOUD_AGENT_ENGINE_ID" not in os.environ:
    os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ID"] = agent_engine_name.split("/")[-1]

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_name
)


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_prompt = schema_manager.generate_system_prompt(
    role_description="You are a helpful Workout & Fitness Coach AI assistant.",
    workflow_description="Analyze the request, consult memories/tools, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image. Set the Image url to that exact https link. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

domain_instruction = (
    "\n\n### MEMORY & ALLERGY SAFETY RULES:\n"
    "1. ALLERGIES & DIETARY RESTRICTIONS: You remember and strictly enforce all user allergies "
    "(e.g., peanuts, tree nuts, dairy, lactose, gluten, shellfish, seafood, eggs, soy, wheat, sesame, or medications), "
    "dietary restrictions, health conditions, and fitness goals from previous conversations.\n"
    "2. SAFETY FIRST: ALWAYS check the preloaded memories retrieved via PreloadMemoryTool before recommending any meals, recipes, "
    "or nutritional guidance. NEVER suggest foods containing ingredients the user is allergic to.\n"
    "3. EXPLICIT RECALL: When a user asks for meal or workout recommendations, acknowledge their remembered allergies and preferences from memory.\n\n"
    "### AVAILABLE TOOLS & CAPABILITIES:\n"
    "- Exercise Lookup & Catalog: Look up exercise details in Firestore (`get_exercise_details`), list exercises by category (`list_exercises`), add new exercises (`add_exercise`).\n"
    "- Workout & Nutrition Calculations: Compute calorie burn, target macros, and workout metrics (`calculate_workout_metrics`).\n"
    "- Food Facts & Nutrition: Fetch real nutritional info for foods using Open Food Facts API (`fetch_food_nutrition_info`).\n"
    "- Nearby Fitness Centers: Geocode addresses (`geocode_address`) and locate nearby gyms/studios (`find_nearby_places`).\n"
    "- Visual & Video Generation: Generate high-quality fitness visuals and video demonstrations saved as artifacts and uploaded to Cloud Storage (`generate_fitness_image`, `generate_domain_image`, `generate_domain_video`).\n"
    "- Python Sandbox: Safely execute custom Python calculations in an Agent Engine sandbox."
)

instruction = a2ui_prompt + domain_instruction


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        client_kwargs={"vertexai": True},
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        get_exercise_details,
        list_exercises,
        add_exercise,
        calculate_workout_metrics,
        generate_fitness_image,
        fetch_food_nutrition_info,
        geocode_address,
        find_nearby_places,
        generate_domain_image,
        generate_domain_video,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)








app = App(
    root_agent=root_agent,
    name="app",
)

