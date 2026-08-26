// Student Node 1개 생성
CREATE (student:Student {
    student_id: 1,
    name: "홍길동",
    age: 25
})
RETURN student;

// Student Node 1개, Course Node 2개, Instructor Node 1개 생성
CREATE
    (student:Student {
        student_id: 2,
        name: "김영희",
        age: 28
    }),
    (python:Course {
        course_id: 101,
        name: "Python",
        level: "입문"
    }),
    (database:Course {
        course_id: 102,
        name: "Database",
        level: "중급"
    }),
    (instructor:Instructor {
        instructor_id: 1,
        name: "Capybara",
        career: 3
    })
RETURN student, python, database, instructor;

// Node 조회
MATCH (node)
RETURN node;

// 학생과 강의 연결 관계 생성 : (홍길동) - [:ENROLLED_IN] → (Python)
MATCH (student:Student {student_id: 1})
MATCH (course:Course {course_id: 101})
CREATE
    (student)-[:ENROLLED_IN {
        score: 95,
        enrolled_at: date("2026-08-01")
    }]->(course)
RETURN student, course;

// (김영희) - [:ENROLLED_IN] → (Database)
MATCH (student:Student {student_id: 2})
MATCH (course:Course {course_id: 102})
CREATE
    (student)-[:ENROLLED_IN {
        score: 88,
        enrolled_at: date("2026-08-02")
    }]->(course)
RETURN student, course;

// 강사와 강의 연결 관계 생성 : (Capybara)-[:TEACHES]->(Python) / (Capybara)-[:TEACHES]->(Database)
MATCH (instructor:Instructor {instructor_id: 1})
MATCH (python:Course {course_id: 101})
MATCH (database:Course {course_id: 102})
CREATE
    (instructor)-[:TEACHES]->(python),
    (instructor)-[:TEACHES]->(database)
RETURN instructor, python, database;

// 전체 그래프 확인
MATCH (node)-[relationship]->(connected_node)
RETURN node, relationship, connected_node;

// 노드 속성 수정
MATCH (student:Student {student_id: 1})
SET student.age = 26
RETURN student;

// 새로운 노드 속성 추가
MATCH (student:Student {student_id: 1})
SET student.status = "수강중"
RETURN student;

// 여러 노드 속성 수정
MATCH (course:Course {course_id: 101})
SET
    course.level = "초급",
    course.duration = 40
RETURN course;

// 관계 속성 수정
MATCH
    (:Student {student_id: 2})
    -[enrollment:ENROLLED_IN]->
    (:Course {course_id: 102})
SET enrollment.score = 92
RETURN enrollment;

// 노드 속성 제거
MATCH (student:Student {student_id: 1})
REMOVE student.status
RETURN student;

// MERGE 2번 실행하여 ON MATCH SET으로 속성 수정
MERGE (course:Course {course_id: 103})
ON CREATE SET
    course.name = "Machine Learning",
    course.level = "입문",
    course.status = "새로 생성"
ON MATCH SET
    course.status = "기존 데이터 조회"
RETURN course;

// 최종 그래프 확인
MATCH (node)
OPTIONAL MATCH (node)-[relationship]->(connected)
RETURN node, relationship, connected;