from xmlrpc.client import DateTime

import bcrypt
from sqlalchemy import Column, Integer, Float, String, Boolean, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship, backref
from testapp import app, db
from datetime import datetime
from flask_login import UserMixin
import hashlib
import enum


# DemoUser --------------------------------------------------------------------------------------------------------------------------------------
class UserRole(enum.Enum):
    ADMIN = 1
    STAFF = 2
    TEACHER = 3

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(500), nullable=False)
    active = Column(Boolean, default=True)
    user_role = Column(Enum(UserRole, nullable=False))

    @staticmethod
    def hash_password(password):
        """Hàm băm mật khẩu sử dụng bcrypt"""
        # Băm mật khẩu với bcrypt
        salt = bcrypt.gensalt()  # Tạo salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')  # Trả về mật khẩu băm dưới dạng string

    @staticmethod
    def check_password(stored_password, input_password):
        """Kiểm tra mật khẩu nhập vào với mật khẩu đã băm"""
        return bcrypt.checkpw(input_password.encode('utf-8'), stored_password.encode('utf-8'))

    def __str__(self):
        return self.name

class Admin(User):
    __tablename__ = 'admin'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    ho = Column(String(50))
    ten = Column(String(50))
    permissions = Column(String(255))

class Staff(User):
    __tablename__ = 'staff'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    ho = Column(String(50))
    ten = Column(String(50))

class Teacher(User):
    __tablename__ = 'teacher'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    ho = Column(String(50))
    ten = Column(String(50))
    monhoc_id = Column(Integer, ForeignKey('monhoc.id'), nullable=False)

class MonHoc(db.Model):
    __tablename__ = 'monhoc'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    teachers = relationship('Teacher', backref='monhoc', lazy=True)
    diems = relationship('Diem', backref='monhoc', lazy=True)

class Diem(db.Model):
    __tablename__ = 'diem'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum('15p', '45p', 'ck'), nullable=False)
    value = Column(Float, nullable=False)
    monhoc_id = Column(Integer, ForeignKey('monhoc.id'), nullable=False)
    hocky_id = Column(Integer, ForeignKey('hocky.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)

class HocKy(db.Model):
    __tablename__ = 'hocky'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    diems = relationship('Diem', backref='hocky', lazy=True)

class Student(db.Model):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ho = Column(String(50), nullable=False)
    ten = Column(String(50), nullable=False)
    sex = Column(Enum('Nam', 'Nữ'), nullable=False)
    DoB = Column(DateTime, nullable=False)
    address = Column(String(100), nullable=False)
    sdt = Column(String(20), nullable=False, unique=True)
    email = Column(String(50), nullable=False, unique=True)
    diems = relationship('Diem', backref='student', lazy=True)
    students = relationship('Lop', secondary='lop_student', lazy='subquery',
                            backref=backref('students', lazy=True))

class Grade(db.Model):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    lops = relationship('Lop', backref='grade', lazy=True)

    def __str__(self):
        return self.name

class Lop(db.Model):
    __tablename__ = 'lop'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    siso = Column(Integer, nullable=True)
    grade_id = Column(Integer, ForeignKey('grade.id'), nullable=False)

    def __str__(self):
        return self.name


lop_student = db.Table('lop_student',
                       Column('lop_id', Integer,ForeignKey('lop.id'), primary_key=True),
                       Column('student_id', Integer,ForeignKey('student.id'), primary_key=True))


if __name__ == '__main__':
    with app.app_context():
        # db.create_all()

        # Add User Roles and Users
        admin_user = Admin(name="Admin User", username="admin", password=User.hash_password("admin123"),
                           user_role=UserRole.ADMIN, ho="Nguyen Van", ten="A", permissions="Full Access")
        staff_user = Staff(name="Staff User", username="staff", password=User.hash_password("staff123"),
                           user_role=UserRole.STAFF, ho="Tran Van", ten="B")
        teacher_user = Teacher(name="Ngo Bao Chau", username="ngobaochau", password=User.hash_password("teacher123"),
                               user_role=UserRole.TEACHER, ho="Ngo Bao", ten="Chau", monhoc_id=1)
        teacher_user_2 = Teacher(name="Nguyen Nhat Anh", username="nguyennhatanh",
                                 password=User.hash_password("teacher123"),
                                 user_role=UserRole.TEACHER, ho="Nguyen Nhat", ten="Anh", monhoc_id=2)

        # Add MonHoc (Subjects)
        math_subject = MonHoc(name="Toán")
        literature_subject = MonHoc(name="Ngữ Văn")

        # Add HocKy (Semesters)
        semester_1 = HocKy(name="HK1 2024-2025")
        semester_2 = HocKy(name="HK2 2024-2025")

        # Add Students
        student_1 = Student(ho="Pham", ten="Minh", sex="Nam", DoB=datetime(2010, 5, 15), address="123 Street A",
                            sdt="0123456789", email="minh.pham@example.com")
        student_2 = Student(ho="Nguyen", ten="An", sex="Nữ", DoB=datetime(2011, 3, 22), address="456 Street B",
                            sdt="0987654321", email="an.nguyen@example.com")

        # Add Grades and Classes
        grade_10 = Grade(name="Khối 10")
        grade_11 = Grade(name="Khối 11")
        grade_12 = Grade(name="Khối 12")

        class_10A = Lop(name="10A", siso=40, grade=grade_10)
        class_11B = Lop(name="11B", siso=35, grade=grade_11)
        class_12C = Lop(name="12C", siso=36, grade=grade_12)

        # Associate students with classes
        class_10A.students.append(student_1)
        class_11B.students.append(student_2)

        # Add Diem (Scores)
        score_1 = Diem(type="15p", value=8.5, monhoc=math_subject, hocky=semester_1, student=student_1)
        score_2 = Diem(type="45p", value=6.5, monhoc=math_subject, hocky=semester_1, student=student_1)
        score_3 = Diem(type="ck", value=9, monhoc=math_subject, hocky=semester_1, student=student_1)
        score_4 = Diem(type="15p", value=7.5, monhoc=literature_subject, hocky=semester_1, student=student_1)
        score_5 = Diem(type="45p", value=9, monhoc=literature_subject, hocky=semester_1, student=student_1)
        score_6 = Diem(type="ck", value=9, monhoc=literature_subject, hocky=semester_1, student=student_1)
        score_7 = Diem(type="15p", value=8.5, monhoc=math_subject, hocky=semester_1, student=student_2)
        score_8 = Diem(type="45p", value=6.5, monhoc=math_subject, hocky=semester_1, student=student_2)
        score_9 = Diem(type="ck", value=9, monhoc=math_subject, hocky=semester_1, student=student_2)
        score_10 = Diem(type="15p", value=7.5, monhoc=literature_subject, hocky=semester_1, student=student_2)
        score_11 = Diem(type="45p", value=9, monhoc=literature_subject, hocky=semester_1, student=student_2)
        score_12 = Diem(type="ck", value=9, monhoc=literature_subject, hocky=semester_1, student=student_2)

        # Commit all changes to the database
        db.session.add_all([admin_user, staff_user, teacher_user, teacher_user_2])
        db.session.add_all([math_subject, literature_subject])
        db.session.add_all([semester_1, semester_2])
        db.session.add_all([student_1, student_2])
        db.session.add_all([grade_10, grade_11, grade_12])
        db.session.add_all([class_10A, class_11B, class_12C])
        db.session.add_all([score_1, score_2, score_3, score_4, score_5, score_6, score_7, score_8, score_9, score_10,
                            score_11, score_12])
        db.session.commit()