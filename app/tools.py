"""Firestore tools for reading and writing exercise data."""

import google.auth
from google.adk.tools import ToolContext
from google.cloud import firestore


PROJECT_ID = "qwiklabs-gcp-03-4c4cb745f0b3"


def _get_firestore_client() -> firestore.Client:
    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/datastore",
        ]
    )
    return firestore.Client(project=PROJECT_ID, credentials=creds)


def get_exercise_details(exercise_name_or_id: str) -> str:
    """Retrieves details for a specific exercise from Firestore.

    Args:
        exercise_name_or_id: The ID or name of the exercise to look up (e.g. 'push_up', 'Push-up', 'barbell_squat').

    Returns:
        A string summarizing the exercise details or an error message if not found.
    """
    db = _get_firestore_client()
    doc_id = exercise_name_or_id.lower().replace(" ", "_")

    doc_ref = db.collection("exercises").document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        return (
            f"Exercise: {data.get('name')}\n"
            f"Category: {data.get('category')}\n"
            f"Target Muscle: {data.get('target_muscle')}\n"
            f"Difficulty: {data.get('difficulty')}\n"
            f"Recommended Sets/Reps: {data.get('recommended_sets_reps')}\n"
            f"Description: {data.get('description')}"
        )

    docs = db.collection("exercises").stream()
    matches = []
    for d in docs:
        d_dict = d.to_dict()
        name = d_dict.get("name", "")
        cat = d_dict.get("category", "")
        if (
            exercise_name_or_id.lower() in name.lower()
            or exercise_name_or_id.lower() in cat.lower()
        ):
            matches.append(d_dict)

    if matches:
        res = []
        for data in matches:
            res.append(
                f"- {data.get('name')} ({data.get('category')}): {data.get('target_muscle')} | {data.get('recommended_sets_reps')} | {data.get('description')}"
            )
        return "Found exercises:\n" + "\n".join(res)

    return f"No exercise found matching '{exercise_name_or_id}' in Firestore."


def list_exercises(category: str = "") -> str:
    """Lists exercises stored in Firestore, optionally filtered by category.

    Args:
        category: Optional category filter (e.g. 'Calisthenics', 'Strength', 'Core'). Leave empty to list all.

    Returns:
        A formatted list of exercises available in Firestore.
    """
    db = _get_firestore_client()
    docs = db.collection("exercises").stream()
    results = []

    for d in docs:
        data = d.to_dict()
        cat = data.get("category", "")
        if not category or category.lower() in cat.lower():
            results.append(
                f"- {data.get('name')} [{cat}]: Target: {data.get('target_muscle')} | Difficulty: {data.get('difficulty')}"
            )

    if not results:
        return f"No exercises found in Firestore for category: '{category}'." if category else "No exercises found in Firestore."

    return "Firestore Exercises:\n" + "\n".join(results)


def add_exercise(
    name: str,
    category: str,
    target_muscle: str,
    recommended_sets_reps: str,
    difficulty: str,
    description: str,
) -> str:
    """Adds a new exercise or updates an existing exercise in Firestore.

    Args:
        name: Name of the exercise (e.g. 'Dumbbell Curl').
        category: Category (e.g. 'Strength', 'Calisthenics', 'Cardio', 'Core').
        target_muscle: Target muscle group (e.g. 'Biceps').
        recommended_sets_reps: Recommended sets and reps (e.g. '3 sets of 10-12 reps').
        difficulty: Difficulty level ('Beginner', 'Intermediate', 'Advanced').
        description: Instructions or tips for proper form.

    Returns:
        Confirmation message with the created exercise ID.
    """
    db = _get_firestore_client()
    doc_id = name.lower().replace(" ", "_")

    doc_data = {
        "name": name,
        "category": category,
        "target_muscle": target_muscle,
        "recommended_sets_reps": recommended_sets_reps,
        "difficulty": difficulty,
        "description": description,
    }

    db.collection("exercises").document(doc_id).set(doc_data)
    return f"Successfully added exercise '{name}' (ID: '{doc_id}') to Firestore."


def calculate_workout_metrics(
    user_weight_kg: float,
    exercise_type: str,
    duration_minutes: int,
    goal: str = "maintenance",
) -> str:
    """Calculates estimated calorie burn for an exercise and target daily macros based on user goals.

    Args:
        user_weight_kg: Weight of the user in kilograms (e.g. 70.0).
        exercise_type: Name or type of exercise (e.g. 'push_up', 'barbell_squat', 'running', 'plank', 'calisthenics').
        duration_minutes: Duration of exercise in minutes (e.g. 30).
        goal: Fitness goal - 'fat_loss', 'muscle_gain', or 'maintenance'.

    Returns:
        Formatted summary string with estimated calorie burn and recommended daily macros.
    """
    met_values = {
        "push_up": 8.0,
        "barbell_squat": 6.0,
        "pull_up": 8.0,
        "plank": 3.5,
        "running": 9.8,
        "cycling": 7.5,
        "calisthenics": 8.0,
        "strength": 6.0,
    }

    matched_met = 5.0
    for key, val in met_values.items():
        if key in exercise_type.lower():
            matched_met = val
            break

    calories_burned = round(matched_met * user_weight_kg * (duration_minutes / 60.0), 1)

    if goal.lower() == "fat_loss":
        target_calories = round(user_weight_kg * 28)
        protein_g = round(user_weight_kg * 2.2)
        fat_g = round((target_calories * 0.25) / 9)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4)
    elif goal.lower() == "muscle_gain":
        target_calories = round(user_weight_kg * 36)
        protein_g = round(user_weight_kg * 2.0)
        fat_g = round((target_calories * 0.25) / 9)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4)
    else:
        target_calories = round(user_weight_kg * 32)
        protein_g = round(user_weight_kg * 1.8)
        fat_g = round((target_calories * 0.30) / 9)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4)

    return (
        f"Workout Calculation Summary:\n"
        f"- Exercise: {exercise_type.title()} ({duration_minutes} min at {user_weight_kg} kg)\n"
        f"- Estimated Calorie Burn: {calories_burned} kcal (MET: {matched_met})\n"
        f"- Target Daily Nutrition for '{goal.title()}':\n"
        f"  * Daily Calories: {target_calories} kcal\n"
        f"  * Protein: {protein_g}g\n"
        f"  * Carbs: {carbs_g}g\n"
        f"  * Fat: {fat_g}g"
    )


def generate_fitness_image(title: str, description: str) -> str:
    """Generates an image asset for an exercise form or fitness meal and uploads it to Cloud Storage.

    Args:
        title: Title of the exercise or meal (e.g. 'Push-up Form', 'High Protein Breakfast').
        description: Form instructions or visual details to include in the visual card.

    Returns:
        The public Cloud Storage URL of the generated image asset.
    """
    import uuid
    from google.cloud import storage

    bucket_name = "fitness-coach-assets-qwiklabs-gcp-03-4c4cb745f0b3"
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    storage_client = storage.Client(project=PROJECT_ID, credentials=creds)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
  <rect width="600" height="350" fill="#1e293b" rx="12"/>
  <rect x="20" y="20" width="560" height="310" fill="#0f172a" rx="8" stroke="#38bdf8" stroke-width="2"/>
  <text x="40" y="65" font-family="sans-serif" font-size="24" font-weight="bold" fill="#38bdf8">🏋️ {title}</text>
  <line x1="40" y1="80" x2="560" y2="80" stroke="#334155" stroke-width="2"/>
  <foreignObject x="40" y="100" width="520" height="180">
    <div xmlns="http://www.w3.org/1999/xhtml" style="color:#f8fafc; font-family:sans-serif; font-size:16px; line-height:1.6;">
      {description}
    </div>
  </foreignObject>
  <text x="40" y="310" font-family="sans-serif" font-size="12" fill="#64748b">Fitness Asset | Cloud Storage: gs://{bucket_name}</text>
</svg>"""

    file_id = title.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:8] + ".svg"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_id)
    blob.upload_from_string(svg_content, content_type="image/svg+xml")

    public_url = f"https://storage.googleapis.com/{bucket_name}/{file_id}"
    return f"Successfully generated visual asset for '{title}'. Public URL: {public_url}"


def fetch_food_nutrition_info(query: str) -> str:
    """Searches real nutrition information for a food item using the Open Food Facts public API.

    Args:
        query: Food item or ingredient to search (e.g. 'oats', 'chicken breast', 'banana', 'whey protein').

    Returns:
        A formatted string with product name, calories, protein, carbs, and fat per 100g.
    """
    import os
    import json
    import urllib.parse
    import urllib.request

    # Optional API key support if API requires authentication in future
    api_key = os.environ.get("NUTRITION_API_KEY", "")

    encoded_query = urllib.parse.quote(query)
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_query}&search_simple=1&action=process&json=1"
    headers = {"User-Agent": "FitnessCoachAgent/1.0 (Linux/Python)"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            products = data.get("products", [])

            if not products:
                return f"No nutrition info found for food item: '{query}'."

            results = []
            for p in products[:3]:
                name = p.get("product_name") or p.get("product_name_en")
                if not name:
                    continue
                nut = p.get("nutriments", {})
                kcal = nut.get("energy-kcal_100g") or nut.get("energy-kcal") or "N/A"
                protein = nut.get("proteins_100g") or nut.get("proteins") or "N/A"
                carbs = nut.get("carbohydrates_100g") or nut.get("carbohydrates") or "N/A"
                fat = nut.get("fat_100g") or nut.get("fat") or "N/A"

                results.append(
                    f"• Product: {name}\n"
                    f"  - Calories: {kcal} kcal / 100g\n"
                    f"  - Protein: {protein}g / 100g\n"
                    f"  - Carbs: {carbs}g / 100g\n"
                    f"  - Fat: {fat}g / 100g"
                )

            if not results:
                return f"No nutritional details available for '{query}'."

            return f"Real Nutrition Data for '{query}' (Open Food Facts API):\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error fetching nutrition data for '{query}': {str(e)}"


def geocode_address(address: str) -> str:
    """Converts a human-readable address into geographic coordinates (latitude & longitude) using Google Geocoding API.

    Args:
        address: The address or location string to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        Formatted string containing formatted address, latitude, and longitude.
    """
    import os
    import json
    import urllib.parse
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in the environment."

    encoded_address = urllib.parse.quote(address)
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        with urllib.request.urlopen(geo_url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for address '{address}'. Status: {data.get('status')}"

            res = data["results"][0]
            fmt_address = res.get("formatted_address")
            loc = res["geometry"]["location"]
            lat = loc["lat"]
            lng = loc["lng"]

            return (
                f"Geocoding Result:\n"
                f"- Address: {fmt_address}\n"
                f"- Location: Latitude {lat}, Longitude {lng}\n"
                f"- Raw Coordinates: lat={lat}, lng={lng}"
            )
    except Exception as e:
        return f"Error calling Geocoding API for '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 5000.0,
) -> str:
    """Finds nearby places of a specified type using Google Places API (New).

    Args:
        latitude: Latitude coordinate for search center.
        longitude: Longitude coordinate for search center.
        place_type: Type of place to search for (e.g. 'gym', 'fitness_center', 'park').
        radius_meters: Radius in meters around the center location (default 5000.0).

    Returns:
        A list of matching places with name, formatted address, and location coordinates.
    """
    import os
    import json
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in the environment."

    places_url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    body = json.dumps(
        {
            "includedTypes": [place_type],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_meters,
                }
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(places_url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            places = data.get("places", [])
            if not places:
                return f"No nearby places of type '{place_type}' found within {radius_meters}m."

            results = []
            for p in places[:5]:
                name = p.get("displayName", {}).get("text", "Unknown Place")
                addr = p.get("formattedAddress", "No address")
                loc = p.get("location", {})
                lat = loc.get("latitude")
                lng = loc.get("longitude")

                results.append(
                    f"• {name}\n"
                    f"  - Address: {addr}\n"
                    f"  - Location: ({lat}, {lng})"
                )

            return f"Nearby '{place_type}' Places (Places API New):\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error calling Places API (New): {str(e)}"


def generate_domain_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image for a fitness, workout, or nutrition item using gemini-3.1-flash-lite-image in global region.
    Saves the image with tool_context.save_artifact and uploads it to Cloud Storage, returning its public HTTPS URL.

    Args:
        prompt: Prompt describing the fitness image (e.g. 'Photo of a healthy post-workout protein smoothie bowl').
        tool_context: ADK ToolContext instance for saving artifacts.

    Returns:
        The public HTTPS URL of the uploaded image (https://storage.googleapis.com/<bucket>/<object>).
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    project_id = "qwiklabs-gcp-03-4c4cb745f0b3"
    bucket_name = "fitness-coach-assets-qwiklabs-gcp-03-4c4cb745f0b3"

    client = genai.Client(vertexai=True, project=project_id, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"]
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return "Failed to generate image from gemini-3.1-flash-lite-image model."

    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"fitness_image_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes to public Cloud Storage bucket without writing to local file
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    storage_client = storage.Client(project=project_id, credentials=creds)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    return public_url


def generate_domain_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video for a workout, exercise demonstration, or fitness item using gemini-omni-flash-preview in global region.
    Saves the video with tool_context.save_artifact and uploads it to Cloud Storage, returning its public HTTPS URL.

    Args:
        prompt: Prompt describing the fitness video demonstration (e.g. 'Short video demonstration of a perfect push-up form').
        tool_context: ADK ToolContext instance for saving artifacts.

    Returns:
        The public HTTPS URL of the uploaded video (https://storage.googleapis.com/<bucket>/<object>).
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    project_id = "qwiklabs-gcp-03-4c4cb745f0b3"
    bucket_name = "fitness-coach-assets-qwiklabs-gcp-03-4c4cb745f0b3"

    client = genai.Client(vertexai=True, project=project_id, location="global")
    response = client.models.generate_content(
        model="gemini-omni-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["VIDEO", "TEXT"]
        ),
    )

    video_bytes = None
    mime_type = "video/mp4"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                video_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "video/mp4"
                break

    if not video_bytes:
        return "Failed to generate video from gemini-omni-flash-preview model."

    ext = "mp4"
    if "webm" in mime_type:
        ext = "webm"
    filename = f"fitness_video_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes to public Cloud Storage bucket without writing to local file
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    storage_client = storage.Client(project=project_id, credentials=creds)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    return public_url





