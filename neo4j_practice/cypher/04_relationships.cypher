// 강의와 카테고리 연결 (Course) - [:BELONGS_TO] -> (Category)
MATCH (course:Course {course_id: 101})
MATCH (category:Category {category_id: 201})
MERGE (course)-[:BELONGS_TO]->(category);

MATCH (course:Course {course_id: 102})
MATCH (category:Category {category_id: 202})
MERGE (course)-[:BELONGS_TO]->(category);

MATCH (course:Course {course_id: 104})
MATCH (category:Category {category_id: 203})
MERGE (course)-[:BELONGS_TO]->(category);

MATCH (course:Course)
MATCH (category:Category {category_id: 204})
WHERE course.course_id IN [103,105,106]
MERGE (course)-[:BELONGS_TO]->(category);

MATCH (course:Course)-[relation:BELONGS_TO]->(category:Category)
RETURN course, relation, category;

// 관계 삭제 구문 필요시
// MATCH ()-[relation:BELONGS_TO]-()
// DELETE relation;

// 표 형태로 조회
MATCH (course:Course)-[relation:BELONGS_TO]->(category:Category)
RETURN
    course.course_id AS course_id,
    course.name AS course_name,
    category.category_id AS category_id,
    category.name AS name
ORDER BY course.course_id;


// 강사와 강의 연결
MATCH (instructor1:Instructor {instructor_id: 1})
MATCH (python:Course {course_id: 101})
MATCH (database:Course {course_id: 102})
MERGE (instructor1)-[:TEACHES]->(python)
MERGE (instructor1)-[:TEACHES]->(database);

MATCH (instructor2:Instructor {instructor_id: 2})
MATCH (data_analysis:Course {course_id: 104})
MATCH (machine_learning:Course {course_id: 103})
MERGE (instructor2)-[:TEACHES]->(data_analysis)
MERGE (instructor2)-[:TEACHES]->(machine_learning);

MATCH (instructor3:Instructor {instructor_id: 3})
MATCH (deep_learning:Course {course_id: 105})
MATCH (langchain:Course {course_id: 106})
MERGE (instructor3)-[:TEACHES]->(deep_learning)
MERGE (instructor3)-[:TEACHES]->(langchain);

MATCH (instructor:Instructor)-[relation:TEACHES]->(course:Course)
RETURN instructor, relation, course;


// 학생과 강의 연결
MATCH (student1:Student {student_id: 1})
MATCH (course:Course {course_id: 101})
MERGE (student1)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 95,
    enroll.enrolled_at= date("2026-08-01");

MATCH (student1:Student {student_id: 1})
MATCH (course:Course {course_id: 104})
MERGE (student1)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 90,
    enroll.enrolled_at= date("2026-08-03");

// 김영희
MATCH (student2:Student {student_id: 2})
MATCH (course:Course {course_id: 102})
MERGE (student2)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 92,
    enroll.enrolled_at= date("2026-08-02");

MATCH (student2:Student {student_id: 2})
MATCH (course:Course {course_id: 103})
MERGE (student2)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 89,
    enroll.enrolled_at= date("2026-08-04");

// 이민수
MATCH (student3:Student {student_id: 3})
MATCH (course:Course {course_id: 101})
MERGE (student3)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 85,
    enroll.enrolled_at= date("2026-08-01");

MATCH (student3:Student {student_id: 3})
MATCH (course:Course {course_id: 104})
MERGE (student3)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 91,
    enroll.enrolled_at= date("2026-08-03");

// 박서연
MATCH (student4:Student {student_id: 4})
MATCH (course:Course {course_id: 103})
MERGE (student4)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 94,
    enroll.enrolled_at= date("2026-08-04");

MATCH (student4:Student {student_id: 4})
MATCH (course:Course {course_id: 105})
MERGE (student4)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 88,
    enroll.enrolled_at= date("2026-08-05");

// 최준호
MATCH (student5:Student {student_id: 5})
MATCH (course:Course {course_id: 102})
MERGE (student5)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 86,
    enroll.enrolled_at= date("2026-08-02");

MATCH (student5:Student {student_id: 5})
MATCH (course:Course {course_id: 106})
MERGE (student5)-[enroll:ENROLLED_IN]->(course)
SET
    enroll.score= 93,
    enroll.enrolled_at= date("2026-08-06");

MATCH (student:Student)-[enroll:ENROLLED_IN]->(course:Course)
RETURN
    student.name AS studnet_name,
    course.name AS course_name,
    enroll.score AS score,
    enroll.enrolled_at AS enrolled_at
ORDER BY student.student_id, course.course_id;