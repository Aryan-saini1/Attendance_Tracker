from std_db import AttendanceSystem

# Initialize system
system = AttendanceSystem(user='root', password='saini')

# Modify the students table
system.modify_students_table()
print("Students table modification completed.") 