from sqlmodel import Session, select

from app.domain.observation import Observation
from .database import get_session

class ObservationRepository:

    def save(self, observation: Observation) -> Observation:
        session = get_session()
        session.add(observation)
        session.commit()
        session.refresh(observation)
        return observation
    
    def find_similar(self, embedding: list[float], limit: int = 10) -> list[Observation]:
        statement = (
            select(Observation)
            .order_by(Observation.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        session: Session = get_session()
        return list(session.exec(statement))