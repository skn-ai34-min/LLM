// NODE 이름과 노드별 수 확인
MATCH (node)
RETURN
    labels(node) as labels,
    count(node) as count
ORDER BY labels;

MATCH (student:Student)
WITH
    student.student.id as student_id,
    count(*) as count
WHERE count > 1
RETURN student_id, count;


// 강의 ID가 중복되는 Course Node 검색
MATCH (course:Course)
WITH
    course.course.id as course_id,
    count(*) as count
WHERE count > 1
RETURN course_id, count;