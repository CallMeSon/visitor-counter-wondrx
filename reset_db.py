import sys
from src.db.database import SessionLocal
from src.services.aggregator import EventAggregatorService

def reset_database(event_id: int = 1):
    db = SessionLocal()
    try:
        service = EventAggregatorService(db, event_id)
        summary = service.reset_counter()
        print(f"[SUCCESS] Database untuk Event ID #{event_id} berhasil di-reset ke 0!")
        print(f"Ringkasan: Total Masuk={summary['total_in']}, Total Keluar={summary['total_out']}, Di Dalam={summary['current_inside']}")
    except Exception as e:
        print(f"[ERROR] Gagal mereset database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    event_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    reset_database(event_id)
