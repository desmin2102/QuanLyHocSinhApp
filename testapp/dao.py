


from sqlalchemy.exc import NoResultFound

from testapp.models import *


# load khoi
def load_grade():
    return Grade.query.all()

# load lop
def load_class(grade_id=None):
    if grade_id:
        classes = Lop.query.filter_by(grade_id=grade_id).all()
    else:
        classes = Lop.query.all()
    return classes

# load monhoc
def load_monhoc(grade_id=None):
    return  MonHoc.query.all()


def them_monhoc(name):
    if MonHoc.query.filter_by(name=name).first():
        raise ValueError("Môn học đã tồn tại!")
    new_monhoc = MonHoc(name=name)
    db.session.add(new_monhoc)
    db.session.commit()


def sua_monhoc(id, name):
    # Kiểm tra nếu môn học mới có tên giống với môn học khác
    if MonHoc.query.filter_by(name=name).first():
        raise ValueError("Môn học đã tồn tại!")

    monhoc = MonHoc.query.get(id)
    if monhoc:
        monhoc.name = name
        db.session.commit()
        return True
    return False


def xoa_monhoc(id):
    monhoc = MonHoc.query.get(id)
    if not monhoc:
        return False
    # Kiểm tra nếu môn học liên kết với dữ liệu khác
    if Diem.query.filter_by(monhoc_id=id).first():
        raise ValueError("Không thể xóa môn học vì có dữ liệu liên quan.")
    db.session.delete(monhoc)
    db.session.commit()
    return True


# load hoc sinh
def load_student():
    return Student.query.all()

# Delete student
def xoa_hocsinh(id):
    # Tìm học sinh theo ID
    hocsinh = Student.query.get(id)  # Sử dụng model ORM
    if not hocsinh:
        return False

    try:
        # Xóa dữ liệu liên quan trong bảng Diem
        Diem.query.filter_by(student_id=id).delete()

        # Xóa dữ liệu liên quan trong bảng Lop_Student
        # Lop_Student.query.filter_by(student_id=id).delete()

        # Xóa học sinh
        db.session.delete(hocsinh)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()  # Hoàn tác nếu có lỗi
        raise ValueError(f"Lỗi khi xóa học sinh: {e}")

# add student
def them_hoc_sinh(ho, ten, gioi_tinh, ngay_sinh, dia_chi, sdt, email):
    # Kiểm tra email hợp lệ
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    # Kiểm tra số điện thoại chỉ chứa số
    # Kiểm tra độ tuổi
    dob = datetime.strptime(ngay_sinh, '%Y-%m-%d')  # Chuyển ngày sinh từ chuỗi sang đối tượng datetime
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))  # Tính tuổi chính xác
    if age < 15 or age > 20:
        raise ValueError("Chỉ chấp nhận học sinh từ 15 đến 20 tuổi!")

    # Kiểm tra nếu email đã tồn tại
    if Student.query.filter_by(email=email).first():
        raise ValueError("Email đã tồn tại!")

    #Kiểm tra nếu sđt học sinh đã tồn tại
    if Student.query.filter_by(sdt=sdt).first():
        raise ValueError("SĐT học sinh đã tồn tại!")

    # Thêm học sinh mới
    new_student = Student(
        ho=ho,
        ten=ten,
        sex=gioi_tinh,
        DoB=ngay_sinh,
        address=dia_chi,
        sdt=sdt,
        email=email
    )
    db.session.add(new_student)
    db.session.commit()



# load diem theo mon
def load_diem_theo_mon_hoc(monhoc_id=None):
  return Diem.query.all()


# load user
def load_user():
    return User.query.all()

# load giaovien
def load_teacher():
    return Teacher.query.all()

def get_student_by_id(student_id):
    return Student.query.get(student_id)

# DinhLuan
# Load học kỳ
# def load_hoc_ky():
#     return HocKy.query.all()

# def check_password(Stored_password, entered_password):
#     return check_password_hash(Stored_password, entered_password)


def get_user_by_username(username):
    # Truy vấn cơ sở dữ liệu để lấy thông tin người dùng
    # Ví dụ, trả về một đối tượng người dùng có chứa mật khẩu đã băm
    user = db.session.query(User).filter_by(username=username).first()
    if user:
        return {"id": user.id, "username": user.username, "password": user.password}
    return None

def get_user_by_id(user_id):
    # Lấy thông tin người dùng từ cơ sở dữ liệu dựa trên user_id
    user = User.query.get(user_id)  # Truy vấn cơ sở dữ liệu với user_id
    if user:
        return {
            "id": user.id,
            "name": user.name,
            "job": user.user_role
        }
    return None  # Nếu không tìm thấy người dùng, trả về None

def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username),
                          User.password.__eq__(password))

    if role:
        u = u.filter(User.user_role.__eq__(role))

    return u.first()

def get_user_by_id(user_id):
    # Lấy thông tin người dùng từ cơ sở dữ liệu dựa trên user_id
    user = User.query.get(user_id)  # Truy vấn cơ sở dữ liệu với user_id
    if user:
        return {
            "id": user.id,
            "name": user.name,
            "job": user.user_role
        }
    return None  # Nếu không tìm thấy người dùng, trả về None


# Hàm xóa người dùng theo ID
def delete_user_by_id(user_id):
    try:
        # Tìm người dùng theo ID
        user = User.query.filter_by(id=user_id).one()

        # Xóa người dùng khỏi cơ sở dữ liệu
        db.session.delete(user)
        db.session.commit()
        print(f"Đã xóa người dùng có ID {user_id}")
    except NoResultFound:
        print(f"Không tìm thấy người dùng với ID {user_id}")
        return False
    return True

def save_user(user):
    if user.id:  # Kiểm tra nếu user đã có id, nghĩa là đây là người dùng đã tồn tại
        # Cập nhật thông tin người dùng
        existing_user = User.query.filter_by(id=user.id).first()
        if existing_user:
            existing_user.name = user.name
            existing_user.username = user.username
            existing_user.email = user.email
            existing_user.active = user.active
            existing_user.user_role = user.user_role
            db.session.commit()  # Lưu thay đổi
            print(f"Đã cập nhật thông tin người dùng có ID {user.id}")
        else:
            print(f"Không tìm thấy người dùng có ID {user.id}")
    else:
        # Nếu user chưa có id (người dùng mới), thêm người dùng mới vào cơ sở dữ liệu
        db.session.add(user)
        db.session.commit()  # Lưu bản ghi mới
        print(f"Đã thêm người dùng mới: {user.name}")
# =======
#    return User.query.get(user_id)

# >>>>>>> main
