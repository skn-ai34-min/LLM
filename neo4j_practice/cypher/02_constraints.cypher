// 학생 ID 고유성 제약조건 생성
CREATE CONSTRAINT student_id_unique IF NOT EXISTS
FOR (student:Student)
REQUIRE student.student_id IS UNIQUE;

// 강의 ID 고유성 제약조건 생성
CREATE CONSTRAINT course_id_unique IF NOT EXISTS
FOR (course:Course)
REQUIRE course.course_id IS UNIQUE;

// 강사 ID 고유성 제약조건 생성
CREATE CONSTRAINT instructor_id_unique IF NOT EXISTS
FOR (instructor:Instructor)
REQUIRE instructor.instructor_id IS UNIQUE;

// 카테고리 ID 고유성 제약조건 생성
CREATE CONSTRAINT category_id_unique IF NOT EXISTS
FOR (category:Category)
REQUIRE category.category_id IS UNIQUE;

SHOW CONSTRAINT