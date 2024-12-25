// Tìm kiếm theo tên lớp
function searchTable() {
    var input = document.getElementById("search-input");
    var filter = input.value.toUpperCase();
    var table = document.getElementById("class-table");
    var rows = table.getElementsByTagName("tr");

    for (var i = 1; i < rows.length; i++) {
        var cells = rows[i].getElementsByTagName("td");
        var className = cells[0].textContent || cells[0].innerText;

        if (className.toUpperCase().indexOf(filter) > -1) {
            rows[i].style.display = "";
        } else {
            rows[i].style.display = "none";
        }
    }
}

// Lọc theo Khối lớp
function filterByGrade() {
    var gradeFilter = document.getElementById("filter-grade").value;
    var rows = document.querySelectorAll("#class-table tbody tr");

    rows.forEach(function(row) {
        var grade = row.getAttribute("data-grade");
        if (gradeFilter === "" || grade === gradeFilter) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// Thêm học sinh vào các lớp
async function addStudentsToClasses() {
    const response = await fetch('/add_students', { method: 'POST' });
    const result = await response.json();
    if (result.success) {
        alert('Đã thêm học sinh thành công!');
        location.reload(); // Tải lại trang để cập nhật danh sách
    } else {
        alert('Có lỗi xảy ra: ' + result.message);
    }
}
