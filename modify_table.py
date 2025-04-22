from std_db import AttendanceSystem

# Initialize system
system = AttendanceSystem(user='root', password='hello')

# Modify the attendance table
system.modify_attendance_table()
print("Attendance table modification completed.") 