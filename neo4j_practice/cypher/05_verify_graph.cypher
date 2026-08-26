// 레이블별로 노드 개수 확인
MATCH (node)
UNWIND labels(node) AS label
RETURN
    label,
    count(node) AS count
ORDER BY label;

// 관계 유형별 개수
MATCH ()-[relationship]->()
RETURN
    type(relationship) AS relationship_type,
    count(relationship) AS count
ORDER BY relationship_type;

// 전체 그래프 확인
MATCH path = ()-[]->()
RETURN path;

// 여러 단계 관계 조회
MATCH (student:Student)-[enroll:ENROLLED_IN]->(course:Course)<-[:TEACHES]-(instructor:Instructor)
MATCH (course)-[:BELONGS_TO]->(category:Category)
RETURN
    student.name AS student_name,
    course.name AS course_name,
    instructor.name AS instructor_name,
    category.name AS category_name,
    enroll.score AS score
ORDER BY student.student_id, course.course_id;