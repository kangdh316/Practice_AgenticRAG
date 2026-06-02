from app.config import SIMILARITY_THRESHOLD


def threshold_router(state):

    if state["confidence_score"] >= SIMILARITY_THRESHOLD:
        return "answer"

    return "web_search"