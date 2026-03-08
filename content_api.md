/course
POST
Create a new course with core metadata such as title, description, category, and author.

/courses/{courseId}/lessons
POST
Create a new lesson within an existing course, including lesson title, type, order, and learning objectives.

/content/uploads
POST
Upload lesson content assets (e.g., video, PDF, SCORM package) and return a content reference for lesson attachment.

/courses/{courseId}/publish
POST
Publish a course so it becomes available to learners after validating required lessons and content completeness.
