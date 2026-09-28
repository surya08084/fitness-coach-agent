"""Seed script for populating Firestore with initial exercise data."""

import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-4c4cb745f0b3"

SEEDED_EXERCISES = [
    {
        "id": "push_up",
        "name": "Push-up",
        "category": "Calisthenics",
        "target_muscle": "Chest, Shoulders, Triceps",
        "recommended_sets_reps": "3 sets of 12-15 reps",
        "difficulty": "Beginner",
        "description": "Keep body straight in plank position, lower chest to floor and push up.",
    },
    {
        "id": "barbell_squat",
        "name": "Barbell Squat",
        "category": "Strength",
        "target_muscle": "Quads, Glutes, Lower Back",
        "recommended_sets_reps": "4 sets of 8-10 reps",
        "difficulty": "Intermediate",
        "description": "Barbell across upper back, squat down until thighs parallel to ground, drive through heels.",
    },
    {
        "id": "pull_up",
        "name": "Pull-up",
        "category": "Calisthenics",
        "target_muscle": "Lats, Biceps, Upper Back",
        "recommended_sets_reps": "3 sets of 6-10 reps",
        "difficulty": "Intermediate",
        "description": "Overhand grip on bar, pull body up until chin clears bar, lower down with control.",
    },
    {
        "id": "plank",
        "name": "Plank",
        "category": "Core",
        "target_muscle": "Abs, Core, Lower Back",
        "recommended_sets_reps": "3 sets of 60 seconds hold",
        "difficulty": "Beginner",
        "description": "Forearms on ground, body straight, brace core and hold position.",
    },
]


def seed_database():
    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/datastore",
        ]
    )
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    collection_ref = db.collection("exercises")

    print(f"Seeding exercises into Firestore project '{PROJECT_ID}'...")
    for exercise in SEEDED_EXERCISES:
        doc_id = exercise["id"]
        doc_data = {k: v for k, v in exercise.items() if k != "id"}
        collection_ref.document(doc_id).set(doc_data)
        print(f"  - Seeded exercise: {exercise['name']} (ID: {doc_id})")

    print("Firestore seeding complete!")


if __name__ == "__main__":
    seed_database()
