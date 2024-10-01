from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Строка подключения к базе данных
DATABASE_URL = "postgresql://localhost:5432/postgres"

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Модель для таблицы "bets"
class Bet(Base):
    __tablename__ = "bets"
    id = Column(Integer, primary_key=True, index=True)
    playerId = Column(Integer, nullable=False)
    gameId = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)

# Pydantic-схема для валидации данных при создании и обновлении
class BetCreate(BaseModel):
    playerId: int
    gameId: int
    amount: float

class BetUpdate(BaseModel):
    playerId: int
    gameId: int
    amount: float

    class Config:
        from_attributes = True  # Используем from_attributes вместо orm_mode

# Инициализация FastAPI приложения
app = FastAPI()

# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HAL структура
def generate_hal(bet):
    return {
        "id": bet.id,
        "playerId": bet.playerId,
        "gameId": bet.gameId,
        "amount": bet.amount,
        "_links": {
            "self": {"href": f"/bets/{bet.id}"},
            "update": {"href": f"/bets/{bet.id}"},
            "delete": {"href": f"/bets/{bet.id}"}
        }
    }

# Получение всех ставок с HAL
@app.get("/bets")
def get_bets(db: Session = Depends(get_db)):
    bets = db.query(Bet).all()
    return [generate_hal(bet) for bet in bets]

# Получение ставки по ID с HAL
@app.get("/bets/{bet_id}")
def get_bet(bet_id: int, db: Session = Depends(get_db)):
    bet = db.query(Bet).filter(Bet.id == bet_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    return generate_hal(bet)

# Создание новой ставки с HAL
@app.post("/bets", response_model=BetCreate)
def create_bet(bet: BetCreate, db: Session = Depends(get_db)):
    db_bet = Bet(playerId=bet.playerId, gameId=bet.gameId, amount=bet.amount)
    db.add(db_bet)
    db.commit()
    db.refresh(db_bet)
    return generate_hal(db_bet)

# Обновление существующей ставки с HAL
@app.put("/bets/{bet_id}", response_model=BetUpdate)
def update_bet(bet_id: int, bet: BetUpdate, db: Session = Depends(get_db)):
    db_bet = db.query(Bet).filter(Bet.id == bet_id).first()
    if not db_bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    db_bet.playerId = bet.playerId
    db_bet.gameId = bet.gameId
    db_bet.amount = bet.amount
    db.commit()
    db.refresh(db_bet)
    return generate_hal(db_bet)

# Удаление ставки с HAL
@app.delete("/bets/{bet_id}")
def delete_bet(bet_id: int, db: Session = Depends(get_db)):
    db_bet = db.query(Bet).filter(Bet.id == bet_id).first()
    if not db_bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    db.delete(db_bet)
    db.commit()
    return {"detail": "Bet deleted"}
