from flask import Flask, jsonify, request, render_template
from std_db import Student, AttendanceSystem
from datetime import datetime
import traceback
import time
import pymysql
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize DAO with retry mechanism
def init_system(max_retries=5):
    for attempt in range(max_retries):
        try:
            # First, test if we can connect to MySQL
            test_conn = pymysql.connect(
                host='localhost',
                user='root',
                password='hello',
                connect_timeout=5
            )
            test_conn.close()
            
            # Now initialize our system
            system = AttendanceSystem(user='root', password='hello')
            # Test connection
            conn = system.connect_db()
            if conn:
                conn.close()
                # Ensure database and tables exist
                system.create_database()
                system.create_tables()
                return system
        except pymysql.Error as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(2)  # Wait 2 seconds before retrying
            else:
                print(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                raise
        except Exception as e:
            print(f"Unexpected error during initialization: {str(e)}")
            raise
    return None

# Global system instance
system = None

@app.before_first_request
def initialize_system():
    global system
    if system is None:
        try:
            system = init_system()
            if system is None:
                raise Exception("Failed to initialize database system")
        except Exception as e:
            print(f"System initialization failed: {str(e)}")
            raise

@app.route('/')
def home():
    try:
        if system is None:
            raise Exception("Database system not initialized")
        return render_template('index.html')
    except Exception as e:
        return render_template('error.html', error=str(e))

# ----- Error Handlers -----
@app.errorhandler(500)
def handle_500(error):
    return jsonify({'error': 'Internal server error', 'details': str(error)}), 500

@app.errorhandler(404)
def handle_404(error):
    return jsonify({'error': 'Not found', 'details': str(error)}), 404

# ----- Student Endpoints -----
@app.route('/students', methods=['GET'])
def list_students():
    try:
        if system is None:
            raise Exception("Database system not initialized")
            
        rows = system.list_students()
        students = [
            {'id': r['id'], 'name': r['name'], 'class': r['class']} for r in rows
        ]
        return jsonify(students)
    except Exception as e:
        print(f"Error in list_students: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/students', methods=['POST'])
def create_student():
    try:
        if system is None:
            raise Exception("Database system not initialized")
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['id', 'name', 'class']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        try:
            student_id = int(data['id'])
            student = Student(
                name=data['name'],
                student_class=data['class']
            )
        except ValueError:
            return jsonify({'error': 'ID must be a valid integer'}), 400
        
        try:
            sid = system.add_student(student, student_id)
            row = system.get_student(sid)
            return jsonify({
                'id': row['id'],
                'name': row['name'],
                'class': row['class']
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        print(f"Error in create_student: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/students/<int:sid>', methods=['GET'])
def read_student(sid):
    try:
        row = system.get_student(sid)
        if not row:
            return jsonify({'message': 'Student not found'}), 404
        return jsonify({
            'id': row['id'],
            'name': row['name'],
            'class': row['class']
        })
    except Exception as e:
        print(f"Error in read_student: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/students/<int:sid>', methods=['PUT'])
def update_student(sid):
    try:
        data = request.get_json()
        existing = system.get_student(sid)
        if not existing:
            return jsonify({'message': 'Student not found'}), 404
        updated = Student(
            name=data.get('name'),
            student_class=data.get('class')
        )
        system.update_student(sid, updated)
        row = system.get_student(sid)
        return jsonify({
            'id': row['id'],
            'name': row['name'],
            'class': row['class']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/students/<int:sid>', methods=['DELETE'])
def delete_student(sid):
    try:
        existing = system.get_student(sid)
        if not existing:
            return jsonify({'message': 'Student not found'}), 404
        system.delete_student(sid)
        return jsonify({'message': f'Student id={sid} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----- Attendance Endpoints -----
@app.route('/attendance', methods=['GET'])
def list_all_attendance():
    try:
        if system is None:
            raise Exception("Database system not initialized")
            
        rows = system.list_all_attendance()
        records = [
            {
                'student_id': r['student_id'],
                'name': r['name'],
                'class': r['class'],
                'date': str(r['date']),
                'status': r['status']
            }
            for r in rows
        ]
        return jsonify(records)
    except Exception as e:
        print(f"Error in list_all_attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/attendance', methods=['POST'])
def mark_attendance():
    try:
        if system is None:
            raise Exception("Database system not initialized")
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['student_id', 'date', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        try:
            student_id = int(data['student_id'])
            at_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            status = data['status']
            
            # Validate status
            if status not in ['Present', 'Absent']:
                return jsonify({'error': 'Status must be either Present or Absent'}), 400
                
            # Check if student exists
            student = system.get_student(student_id)
            if not student:
                return jsonify({'error': f'Student with ID {student_id} not found'}), 404
                
            result = system.mark_attendance(student_id, at_date, status)
            if not result:
                return jsonify({'error': 'Failed to mark attendance'}), 500
                
            row = system.get_attendance(student_id, at_date)
            return jsonify({
                'student_id': row['student_id'],
                'date': str(row['date']),
                'status': row['status']
            }), 201
            
        except ValueError as e:
            return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        print(f"Error in mark_attendance: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/attendance/<int:student_id>/<string:date>', methods=['GET'])
def get_attendance(student_id, date):
    try:
        at_date = datetime.strptime(date, '%Y-%m-%d').date()
        row = system.get_attendance(student_id, at_date)
        if not row:
            return jsonify({'message': 'Attendance record not found'}), 404
        return jsonify({
            'student_id': row['student_id'],
            'date': str(row['date']),
            'status': row['status']
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attendance/student/<int:student_id>', methods=['GET'])
def list_attendance_for_student(student_id):
    try:
        rows = system.list_attendance_by_student(student_id)
        records = [{'date': str(r['date']), 'status': r['status']} for r in rows]
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attendance/<int:student_id>/<string:date>', methods=['PUT'])
def update_attendance(student_id, date):
    try:
        at_date = datetime.strptime(date, '%Y-%m-%d').date()
        data = request.get_json()
        existing = system.get_attendance(student_id, at_date)
        if not existing:
            return jsonify({'message': 'Record not found'}), 404
        new_status = data.get('status')
        system.update_attendance(student_id, at_date, new_status)
        row = system.get_attendance(student_id, at_date)
        return jsonify({
            'student_id': row['student_id'],
            'date': str(row['date']),
            'status': row['status']
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/attendance/<int:student_id>/<string:date>', methods=['DELETE'])
def delete_attendance(student_id, date):
    try:
        at_date = datetime.strptime(date, '%Y-%m-%d').date()
        existing = system.get_attendance(student_id, at_date)
        if not existing:
            return jsonify({'message': 'Record not found'}), 404
        system.delete_attendance(student_id, at_date)
        return jsonify({'message': f'Attendance for student {student_id} on {date} deleted'})
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize system before running
    try:
        system = init_system()
        if system is None:
            print("Failed to initialize system. Please check your database connection.")
            exit(1)
        app.run(debug=True, host='0.0.0.0', port=5003)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        exit(1)
