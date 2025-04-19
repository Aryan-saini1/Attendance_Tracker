from std_db import AttendanceSystem

# Initialize system
system = AttendanceSystem(user='root', password='pass')

# Connect to database
conn = system.connect_db()
if conn:
    cursor = conn.cursor()
    # Drop tables
    cursor.execute("DROP TABLE IF EXISTS attendance")
    cursor.execute("DROP TABLE IF EXISTS students")
    conn.commit()
    print("Tables cleared successfully")
    system.disconnect_db(conn)
else:
    print("Failed to connect to database") 