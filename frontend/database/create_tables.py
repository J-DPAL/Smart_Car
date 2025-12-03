from db import get_db_connection

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS car_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            mode TEXT,
            speed INTEGER,
            direction TEXT,
            distance FLOAT,
            obstacle_detected BOOLEAN
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            alert_type TEXT,
            message TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            file_path TEXT,
            label TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            command TEXT,
            value TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            ir_value INTEGER,
            ultrasonic_value FLOAT,
            speed_value INTEGER
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully!")
