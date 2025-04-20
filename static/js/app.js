const API_BASE_URL = 'http://localhost:5003';

// DOM Elements
const studentForm = document.getElementById('studentForm');
const attendanceForm = document.getElementById('attendanceForm');
const studentSelect = document.getElementById('studentSelect');
const attendanceTableBody = document.getElementById('attendanceTableBody');
const editStudentForm = document.getElementById('editStudentForm');
const saveStudentChanges = document.getElementById('saveStudentChanges');

// Initialize date to today
document.getElementById('attendanceDate').valueAsDate = new Date();

// Fetch and display students
async function fetchStudents() {
    try {
        console.log('Fetching students from:', `${API_BASE_URL}/students`);
        const response = await fetch(`${API_BASE_URL}/students`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            throw new Error(errorData.error || 'Failed to fetch students');
        }
        
        const students = await response.json();
        console.log('Received students:', students);
        
        // Update student select dropdown
        studentSelect.innerHTML = '<option value="">Select a student</option>';
        if (students.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No students available';
            option.disabled = true;
            studentSelect.appendChild(option);
            return;
        }
        
        students.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = `${student.name} (${student.class})`;
            studentSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching students:', error);
        showAlert(`Error fetching students: ${error.message}`, 'danger');
    }
}

// Fetch and display attendance records
async function fetchAttendance() {
    try {
        console.log('Fetching attendance from:', `${API_BASE_URL}/attendance`);
        const response = await fetch(`${API_BASE_URL}/attendance`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            throw new Error(errorData.error || 'Failed to fetch attendance records');
        }
        
        const records = await response.json();
        console.log('Received attendance records:', records);
        
        attendanceTableBody.innerHTML = '';
        if (records.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">No attendance records found</td>';
            attendanceTableBody.appendChild(row);
            return;
        }
        
        records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.student_id}</td>
                <td>${record.name}</td>
                <td>${record.class}</td>
                <td>${record.date}</td>
                <td class="status-${record.status.toLowerCase()}">${record.status}</td>
                <td class="action-buttons">
                    <button class="btn btn-sm btn-danger" onclick="deleteAttendance(${record.student_id}, '${record.date}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            attendanceTableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching attendance:', error);
        showAlert(`Error fetching attendance records: ${error.message}`, 'danger');
    }
}

// Add new student
studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const studentId = document.getElementById('studentId').value;
    const name = document.getElementById('studentName').value;
    const studentClass = document.getElementById('studentClass').value;
    
    if (!studentId || !name || !studentClass) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }
    
    const studentData = {
        id: parseInt(studentId),
        name: name,
        class: studentClass
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/students`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Student added successfully!', 'success');
            studentForm.reset();
            // Refresh the student list
            await fetchStudents();
        } else {
            throw new Error(data.error || 'Failed to add student');
        }
    } catch (error) {
        console.error('Error adding student:', error);
        showAlert(error.message || 'Error adding student', 'danger');
    }
});

// Mark attendance
attendanceForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const studentId = studentSelect.value;
    if (!studentId) {
        showAlert('Please select a student', 'warning');
        return;
    }
    
    const attendanceData = {
        student_id: parseInt(studentId),
        date: document.getElementById('attendanceDate').value,
        status: document.querySelector('input[name="status"]:checked').value
    };
    
    console.log('Submitting attendance data:', attendanceData);
    
    try {
        const response = await fetch(`${API_BASE_URL}/attendance`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(attendanceData)
        });
        
        console.log('Attendance response status:', response.status);
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            throw new Error(errorData.error || 'Failed to mark attendance');
        }
        
        showAlert('Attendance marked successfully', 'success');
        attendanceForm.reset();
        document.getElementById('attendanceDate').valueAsDate = new Date();
        fetchAttendance();
    } catch (error) {
        console.error('Error marking attendance:', error);
        showAlert(`Error marking attendance: ${error.message}`, 'danger');
    }
});

// Delete attendance record
async function deleteAttendance(studentId, date) {
    if (!confirm('Are you sure you want to delete this attendance record?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/attendance/${studentId}/${date}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('Attendance record deleted successfully', 'success');
            fetchAttendance();
        } else {
            throw new Error('Failed to delete attendance record');
        }
    } catch (error) {
        console.error('Error deleting attendance:', error);
        showAlert('Error deleting attendance record', 'danger');
    }
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// Initialize
fetchStudents();
fetchAttendance(); 