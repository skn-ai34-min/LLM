// 학생 노드가 없으면 생성, 있으면 유지
MERGE (student1:Student {student_id: 1})
SET
    student1.name = "홍길동",
    student1.age = 28;

MERGE (student2:Student {student_id: 2})
SET
    student2.name = "김영희",
    student2.age = 28;

MERGE (student3:Student {student_id: 3})
SET
    student3.name = "이민수",
    student3.age = 24;

MERGE (student4:Student {student_id: 4})
SET
    student4.name = "박서연",
    student4.age = 27;
    
MERGE (student5:Student {student_id: 5})
SET
    student5.name = "최준호",
    student5.age = 30;

// student 노드 확인
MERGE (stduent:Student)
RETURN stduent;



// 강의 노드가 없으면 생성, 있으면 유지
MERGE (course1:Course {course_id: 101})
SET
    course1.name = "Python",
    course1.level = "초급",
    course1.duration = 40;

MERGE (course2:Course {course_id: 102})
SET
    course2.name = "Database",
    course2.level = "중급",
    course2.duration = 36;

MERGE (course3:Course {course_id: 103})
SET
    course3.name = "Machine Learning",
    course3.level = "입문",
    course3.duration = 48;

MERGE (course4:Course {course_id: 104})
SET
    course4.name = "Data Analysis",
    course4.level = "입문",
    course4.duration = 40;

MERGE (course5:Course {course_id: 105})
SET
    course5.name = "Deep Learning",
    course5.level = "중급",
    course5.duration = 52;

MERGE (course6:Course {course_id: 106})
SET
    course6.name = "LangChain",
    course6.level = "중급",
    course6.duration = 32;

MATCH (course:Course)
RETURN course;

// Course Node status 속성 제거
MATCH (course:Course {course_id: 103})
REMOVE course.status;

MERGE (instructor1:Instructor {instructor_id: 1})
SET instructor1.name = "Capybara", instructor1.career = 3;

MERGE (instructor2:Instructor {instructor_id: 2})
SET instructor2.name = "Alice", instructor2.career = 7;

MERGE (instructor3:Instructor {instructor_id: 3})
SET instructor3.name = "Bob", instructor3.career = 5;

MATCH (ins:Instructor)
RETURN ins;

// 카테고리 노드가 없으면 생성, 있으면 유지
MERGE (:Category {category_id: 201, name: "프로그래밍"});
MERGE (:Category {category_id: 202, name: "데이터베이스"});
MERGE (:Category {category_id: 203, name: "데이터 분석"});
MERGE (:Category {category_id: 204, name: "인공지능"});
MATCH (ca:Category)
RETURN ca;