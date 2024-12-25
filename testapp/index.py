from functools import wraps

from flask_login import login_user

from testapp import app, dao
from flask import request, render_template, session, redirect, url_for, flash,  logging
from testapp.admin import *
from testapp.dao import get_user_by_id, xoa_hocsinh
from testapp.models import  User, lop_student, UserRole
# =======
# from testapp import app, dao, login
# from flask import request, render_template, session, redirect, url_for, flash, jsonify
# from testapp.admin import *
# # DinhLuan
# from testapp.dao import get_user_by_id
# from testapp.models import Diem, MonHoc, User
# >>>>>>> main
import pandas as pd
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from flask import jsonify
import logging


# Đặt khóa bí mật (secret key) cho ứng dụng Flask
app.secret_key = 'secret_key'  # Dùng để mã hóa thông tin session

# Thời gian hết hạn session (ví dụ 1 giờ)
app.permanent_session_lifetime = timedelta(hours=1)

# Tạo Decorator kiểm tra đăng nhập
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('view_login'))  # Nếu không đăng nhập, chuyển hướng đến trang login
        return f(*args, **kwargs)
    return decorated_function
# =======
# from testapp.models import UserRole
# from testapp.models import Diem, MonHoc
# import pandas as pd
# from sqlalchemy.exc import IntegrityError
# from datetime import datetime
# from flask_login import login_user
# >>>>>>> main

@app.route("/")
@login_required
def index():
    # Kiểm tra nếu người dùng đã đăng nhập (kiểm tra session)
    if 'user_id' in session:
        user_id = session['user_id']
        user = get_user_by_id(user_id)
        if user:
            return render_template('index.html', user=user)
        else:
            return redirect(url_for('view_login'))  # Chuyển hướng nếu không tìm thấy user
    else:
        return redirect(url_for('view_login'))  # Nếu chưa đăng nhập, chuyển hướng đến trang login


@app.route("/grade")
@login_required
def view_grade():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu
    grades = dao.load_grade()
    return render_template('grade.html', grades=grades, user=user)

@app.route("/class")
@login_required
def view_class():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu

    # Lấy danh sách các khối
    grades = dao.load_grade()  # Đây là nơi bạn cần chắc chắn rằng có danh sách khối từ dao

    grade_id = request.args.get('grade_id')
    classes = dao.load_class(grade_id)

    return render_template('class.html', classes=classes, grades=grades, user=user)

@app.route('/class/<int:class_id>')
def class_detail(class_id):
    class_obj = Lop.query.get_or_404(class_id)
    students = class_obj.students
    user = session.get('user')  # Lấy thông tin người dùng từ session
    return render_template('class_detail.html', class_obj=class_obj, students=students, user=user)

@app.route("/lop/<int:lop_id>/students", methods=['GET'])
@login_required
def get_students_by_lop(lop_id):
    lop = Lop.query.get(lop_id)
    if not lop:
        return jsonify({"error": "Lớp không tồn tại"}), 404

    students = [{
        "id": s.id,
        "ho": s.ho,
        "ten": s.ten,
        "dob": s.DoB.strftime('%Y-%m-%d') if s.DoB else None,
        "sex": s.sex,
        "address": s.address
    } for s in lop.students]

    return jsonify({"students": students}), 200

@app.route('/students/not-in-class', methods=['GET'])
@login_required
def get_students_not_in_class():
    try:
        # Truy vấn học sinh không thuộc lớp nào
        students = Student.query.filter(~Student.students.any()).all()
        student_list = [{
            "id": s.id,
            "ho": s.ho,
            "ten": s.ten,
            "dob": s.DoB.strftime('%Y-%m-%d') if s.DoB else None,
            "sex": s.sex
        } for s in students]
        return jsonify({"students": student_list}), 200
    except Exception as e:
        logging.error(f"Error fetching students not in class: {e}", exc_info=True)
        return jsonify({"error": "Unable to fetch data"}), 500

@app.route('/lop/add-students', methods=['POST'])
@login_required
def add_students_to_class():
    try:
        # Lấy dữ liệu từ request
        data = request.get_json()
        class_id = data.get("class_id")
        student_ids = data.get("student_ids")

        # Kiểm tra dữ liệu đầu vào
        if not (class_id and student_ids):
            return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

        # Lấy lớp học từ database
        lop = Lop.query.get(class_id)
        if not lop:
            return jsonify({"error": "Lớp không tồn tại"}), 404

        # Thêm học sinh vào lớp (lop_student)
        for student_id in student_ids:
            # Kiểm tra xem ID học sinh có hợp lệ hay không
            student = Student.query.get(student_id)
            if not student:
                continue

            # Kiểm tra nếu học sinh đã tồn tại trong lớp
            connection_exists = db.session.query(lop_student).filter_by(
                lop_id=class_id, student_id=student_id).first()
            if not connection_exists:
                # Thêm vào bảng trung gian lop_student
                insert_stmt = lop_student.insert().values(lop_id=class_id, student_id=student_id)
                db.session.execute(insert_stmt)

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        logging.error(f"Lỗi xảy ra: {str(e)}")
        return jsonify({"error": "Có lỗi xảy ra khi thêm học sinh"}), 500

#Đếm số học sinh đang có
@app.route('/class', methods=['GET'])
@login_required
def class_list():
    classes = Lop.query.all()

    class_data = []
    for lop in classes:
        # Sử dụng thuộc tính `siso` để lấy sĩ số thực tế
        class_data.append({
            "id": lop.id,
            "name": lop.name,
            "siso": lop.siso  # Tính sĩ số thực tế
        })

    return render_template('class.html', classes=class_data)
@app.route('/lop/<int:lop_id>/count', methods=['GET'])
@login_required
def get_student_count(lop_id):
    siso = db.session.query(lop_student).filter(lop_student.c.lop_id == lop_id).count()
    return jsonify({"siso": siso})



@app.route('/lop/<int:lop_id>/remove-student/<int:student_id>', methods=['DELETE'])
@login_required
def remove_student_from_class(lop_id, student_id):
    try:
        # Kiểm tra xem lớp có tồn tại hay không
        lop = Lop.query.get(lop_id)
        if not lop:
            return jsonify({"error": "Lớp không tồn tại"}), 404

        # Kiểm tra xem học sinh có trong lớp hay không
        student_in_class = db.session.query(lop_student).filter_by(lop_id=lop_id, student_id=student_id).first()
        if not student_in_class:
            return jsonify({"error": "Học sinh không thuộc lớp này"}), 404

        # Xóa quan hệ trong bảng lop_student
        db.session.query(lop_student).filter_by(lop_id=lop_id, student_id=student_id).delete()
        db.session.commit()

        return jsonify({"success": True}), 200

    except Exception as e:
        logging.error(f"Lỗi khi xóa học sinh khỏi lớp: {str(e)}")
        return jsonify({"error": "Không thể xóa học sinh khỏi lớp"}), 500


# @app.route('/lop/<int:lop_id>/students', methods=['GET'])
# @login_required
# def get_students_in_class(lop_id):
#     session = db.session
#     lop = session.get(Lop, lop_id)  # Thay đổi từ Lop.query.get(lop_id)
#
#     if not lop:
#         return jsonify({"error": "Lớp không tồn tại"}), 404
#
#     students = [
#         {
#             "id": student.id,
#             "ho": student.ho,
#             "ten": student.ten,
#             "dob": student.DoB.strftime('%Y-%m-%d') if student.DoB else None,
#             "sex": student.sex,
#             "address": student.address,
#         }
#         for student in lop.students
#     ]
#     return jsonify({"students": students}), 200
#

# @app.route("/user")
# def view_user():
#     return render_template('user')

@app.route("/teacher")
@login_required
def view_teacher():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu

    teachers = dao.load_teacher()
    return render_template('teacher.html', teachers=teachers, user=user)

@app.route("/student")
@login_required
def view_student():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu
    students = dao.load_student()
    return render_template('student.html', students=students, user=user)
# Phân trang
@app.route('/students', methods=['GET'])
@login_required
def get_students():
    page = request.args.get('page', 1, type=int)  # Trang hiện tại
    per_page = request.args.get('per_page', 10, type=int)  # Số lượng mỗi trang

    students_query = Student.query
    total = students_query.count()
    students = students_query.paginate(page=page, per_page=per_page, error_out=False)

    data = [{
        "id": s.id,
        "ho": s.ho,
        "ten": s.ten,
        "sex": s.sex,
        "dob": s.DoB.strftime('%Y-%m-%d'),
        "address": s.address,
        "sdt": s.sdt,
        "email": s.email
    } for s in students.items]

    return jsonify({
        "students": data,
        "total": total,
        "page": page,
        "pages": students.pages
    })

@app.route("/them_students", methods=['POST'])
@login_required
def them_student():
    try:
        data = request.get_json()
        ho = data.get("ho")
        ten = data.get("ten")
        sex = data.get("gender")  # Đổi gioi_tinh thành sex
        ngay_sinh = data.get("dob")
        dia_chi = data.get("address")
        sdt = data.get("phone")
        email = data.get("email")

        if not (ho and ten and sex and ngay_sinh and dia_chi and sdt and email):
            return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

        dao.them_hoc_sinh(ho, ten, sex, ngay_sinh, dia_chi, sdt, email)
        return jsonify({"success": True}), 200


    except ValueError as e:

        logging.error(f"Validation error: {e}", exc_info=True)

        return jsonify({"error": str(e)}), 400

    except Exception as e:

        logging.error(f"Unexpected error: {e}", exc_info=True)

        return jsonify({"error": "Có lỗi xảy ra"}), 500

@app.route("/edit_student/<int:student_id>", methods=['PUT'])
@login_required
def edit_student(student_id):
    try:
        data = request.get_json()
        ho = data.get("ho")
        ten = data.get("ten")
        gioi_tinh = data.get("gender")
        ngay_sinh = data.get("dob")
        dia_chi = data.get("address")
        sdt = data.get("phone")
        email = data.get("email")

        if not (ho and ten and gioi_tinh and ngay_sinh and dia_chi and sdt and email):
            return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Học sinh không tồn tại"}), 404

            # Kiểm tra tuổi
        dob_date = datetime.strptime(ngay_sinh, "%Y-%m-%d")  # Chuyển ngày sinh thành đối tượng datetime
        current_date = datetime.now()
        age = current_date.year - dob_date.year - (
                    (current_date.month, current_date.day) < (dob_date.month, dob_date.day))

        if age < 15 or age > 20:
            return jsonify({"error": "Học sinh phải từ 15 đến 20 tuổi"}), 400

        # Kiểm tra nếu số điện thoại đã tồn tại cho một học sinh khác
        existing_phone = Student.query.filter(Student.sdt == sdt, Student.id != student_id).first()
        if existing_phone:
            return jsonify({"error": "Số điện thoại đã tồn tại!"}), 400

        # Kiểm tra nếu email đã tồn tại cho một học sinh khác
        existing_email = Student.query.filter(Student.email == email, Student.id != student_id).first()
        if existing_email:
            return jsonify({"error": "Email đã tồn tại!"}), 400


        # Cập nhật thông tin học sinh
        student.ho = ho
        student.ten = ten
        student.sex = gioi_tinh
        student.DoB = ngay_sinh
        student.address = dia_chi
        student.sdt = sdt
        student.email = email

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Có lỗi xảy ra"}), 500

@app.route("/delete_student/<int:student_id>", methods=['DELETE'])
@login_required
def delete_student(student_id):
    try:
        if xoa_hocsinh(student_id):
            return jsonify({"success": True, "message": "Học sinh đã được xóa thành công"}), 200
        else:
            return jsonify({"error": "Học sinh không tồn tại"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Có lỗi xảy ra, không thể xóa học sinh"}), 500


@app.route("/diem", methods=["GET", "POST"])
@login_required
def view_diem():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu
    if request.method == "POST":
        lop_id = request.form.get("lop")
        monhoc_id = request.form.get("monhoc")
        hoc_ky_id = request.form.get("hoc_ky")

        # Truy vấn cơ sở dữ liệu để lấy bảng điểm
        diems = dao.load_diem_theo_lop_mon_hoc_hoc_ky(lop_id, monhoc_id, hoc_ky_id)

        return render_template('diem.html', diems=diems, user=user)

    # Lấy danh sách lớp, môn học và học kỳ để hiển thị trong dropdown
    danh_sach_lop = dao.load_class()
    danh_sach_mon_hoc = dao.load_monhoc()
    danh_sach_hoc_ky = dao.load_hoc_ky()

    return render_template('diem.html',
                           danh_sach_lop=danh_sach_lop, danh_sach_mon_hoc=danh_sach_mon_hoc,
                           danh_sach_hoc_ky=danh_sach_hoc_ky, user=user)

# monhoc
@app.route("/monhoc")
@login_required
def view_monhoc():
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Lấy thông tin người dùng từ cơ sở dữ liệu

    monhocs = dao.load_monhoc()
    return render_template('monhoc.html',monhocs=monhocs, user=user)


@app.route("/them_monhoc", methods=['POST'])
@login_required
def them_monhoc():


    data = request.get_json()
    name = data.get("name")

    try:
        if name:
            dao.them_monhoc(name)  # Gọi hàm thêm môn học
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Invalid input"}), 400
    except ValueError as e:  # Bắt lỗi nếu môn học đã tồn tại
        return jsonify({"error": str(e)}), 400



@app.route("/sua_monhoc/<int:id>", methods=['PUT'])
def sua_monhoc(id):
    data = request.get_json()
    name = data.get("name")

    try:
        if dao.sua_monhoc(id, name):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400  # Trả về lỗi nếu môn học đã tồn tại


@app.route("/xoa_monhoc/<int:id>", methods=['DELETE'])
def xoa_monhoc(id):
    if dao.xoa_monhoc(id):
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Not found"}), 404

# monhoc

@app.route("/login", methods=['GET', 'POST'])
def view_login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print("Received data:", data)  # Log kiểm tra dữ liệu

            username = data.get('username')
            password = data.get('password')

            # Kiểm tra dữ liệu có đầy đủ không
            if not username or not password:
                return jsonify({"success": False, "error": "Tên đăng nhập và mật khẩu không được để trống"}), 400

            # Lấy thông tin người dùng từ cơ sở dữ liệu
            user = dao.get_user_by_username(username)
            print("User from database:", user)  # Log kiểm tra dữ liệu người dùng

            if user and User.check_password(user["password"], password):
                session.permanent = True
                session['user_id'] = user['id']
                return jsonify({"success": True}), 200
            else:
                return jsonify({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không chính xác"}), 400
        except Exception as e:
            print("Error during login:", str(e))  # Log lỗi server
            return jsonify({"success": False, "error": "Lỗi hệ thống"}), 500

    return render_template('login.html')





@app.route("/logout")
def logout():
    session.clear()  # Xóa toàn bộ session
    flash("Bạn đã đăng xuất thành công!", "success")
    return redirect(url_for('view_login'))  # Chuyển hướng về trang login


@app.route('/upload', methods=['GET', 'POST'])
def upload_students():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash("Vui lòng chọn file!", "error")
            return redirect(request.url)

        try:
            # Đọc file Excel bằng pandas
            df = pd.read_excel(file)

            # Kiểm tra và ánh xạ cột nếu cần
            required_columns = ['ho', 'ten', 'sex', 'DoB', 'address', 'sdt', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Các cột sau bị thiếu trong file Excel: {', '.join(missing_columns)}")

            # Duyệt từng dòng và thêm vào database
            for _, row in df.iterrows():
                # Tính tuổi từ ngày sinh
                dob = pd.to_datetime(row['DoB'])
                current_date = datetime.now()
                age = (current_date - dob).days // 365  # Tính tuổi bằng số ngày chia cho 365

                # Kiểm tra điều kiện độ tuổi
                if age < 15 or age > 20:
                    flash(f"Học sinh {row['ho']} {row['ten']} không trong độ tuổi từ 15 đến 20.", "warning")
                    continue  # Bỏ qua học sinh này

                # Thêm học sinh vào database nếu hợp lệ
                student = Student(
                    ho=row['ho'],
                    ten=row['ten'],
                    sex=row['sex'],
                    DoB=dob,
                    address=row['address'],
                    sdt=row['sdt'],
                    email=row['email']
                )
                db.session.add(student)

            # Lưu các thay đổi
            db.session.commit()
            flash("Thêm học sinh thành công!", "success")
            return redirect(url_for('upload_students'))

        except ValueError as ve:
            flash(str(ve), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Lỗi: Trùng lặp hoặc dữ liệu không hợp lệ!", "error")
        except Exception as e:
            flash(f"Lỗi không xác định: {str(e)}", "error")

    return render_template('upload.html')

@app.route("/login", methods=['get', 'post'])
def login_view():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)

            next = request.args.get('next')
            return redirect(next if next else '/')

    return render_template('login.html')

@app.route('/login-admin', methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
    if user:
        login_user(user=user)

    return redirect('/admin')

# @login.user_loader
# def load_user(user_id):
#     return dao.get_user_by_id(user_id)

if __name__ == '__main__':
    app.run(debug=True)