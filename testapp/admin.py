from testapp import app, db
from flask_admin import Admin
from testapp.models import Grade, Lop, Student
from flask_admin.contrib.sqla import ModelView

# name là tên trang Admin
admin = Admin(app=app, name='Student Management', template_mode='bootstrap4')

class GradeView(ModelView):
    pass

class LopView(ModelView):
    # fix TH không hiện khoá ngoại trên trang Admin
    form_columns = ["name", "siso", "grade_id"]
    column_list = ["name", "siso", "grade_id"]

admin.add_view(GradeView(Grade, db.session))
admin.add_view(LopView(Lop, db.session))
admin.add_view(ModelView(Student, db.session))