import csv
import io
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class Student:
    def __init__(self, student_id: str, first_name: str, last_name: str,
                 email: str = "", address: str = "", phone: str = "",
                 enrollment_status: str = "active",
                 date_of_birth: Optional[str] = None):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.address = address
        self.phone = phone
        self.enrollment_status = enrollment_status
        self.date_of_birth = date_of_birth

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "address": self.address,
            "phone": self.phone,
            "enrollment_status": self.enrollment_status,
            "date_of_birth": self.date_of_birth
        }


class Grade:
    def __init__(self, student_id: str, course_name: str, teacher_name: str,
                 term: str, grade: float, assigned_date: str = None):
        self.student_id = student_id
        self.course_name = course_name
        self.teacher_name = teacher_name
        self.term = term
        self.grade = grade
        self.assigned_date = assigned_date or datetime.now().strftime("%Y-%m-%d")

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "course_name": self.course_name,
            "teacher_name": self.teacher_name,
            "term": self.term,
            "grade": self.grade,
            "assigned_date": self.assigned_date
        }


class Schedule:
    def __init__(self, schedule_id: str, course_name: str, teacher_name: str,
                 room: str, day: str, start_time: str, end_time: str,
                 student_ids: List[str] = None):
        self.schedule_id = schedule_id
        self.course_name = course_name
        self.teacher_name = teacher_name
        self.room = room
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.student_ids = student_ids or []

    def to_dict(self):
        return {
            "schedule_id": self.schedule_id,
            "course_name": self.course_name,
            "teacher_name": self.teacher_name,
            "room": self.room,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "student_ids": self.student_ids
        }


class ReportGenerator:
    @staticmethod
    def generate_grade_report(students: Dict[str, Student],
                              grades: Dict[str, Grade],
                              term: str,
                              output_path: str = "grade_report.csv") -> str:
        report_buffer = io.StringIO()

        writer = csv.writer(report_buffer)
        writer.writerow(["Student ID", "First Name", "Last Name",
                         "Email", "Phone", "Enrollment Status",
                         "Course", "Teacher", "Grade"])

        student_grade_sum = {}
        student_grade_count = {}

        for grade in grades.values():
            if grade.term != term:
                continue
            student = students.get(grade.student_id)
            if not student:
                continue
            if student.enrollment_status != "active":
                continue

            writer.writerow([
                student.student_id,
                student.first_name,
                student.last_name,
                student.email,
                student.phone,
                student.enrollment_status,
                grade.course_name,
                grade.teacher_name,
                f"{grade.grade:.2f}"
            ])

            if student.student_id not in student_grade_sum:
                student_grade_sum[student.student_id] = 0.0
                student_grade_count[student.student_id] = 0

            student_grade_sum[student.student_id] += grade.grade
            student_grade_count[student.student_id] += 1

        writer.writerow([])
        writer.writerow(["Student Averages"])
        writer.writerow(["Student ID", "First Name", "Last Name", "Average"])
        for sid in students:
            if sid in student_grade_sum:
                student = students[sid]
                if student.enrollment_status != "active":
                    continue
                avg = student_grade_sum[sid] / student_grade_count[sid]

