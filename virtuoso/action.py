from virtuoso import core

def recommend(session: core.Session, course: str) -> list:
    session.get()