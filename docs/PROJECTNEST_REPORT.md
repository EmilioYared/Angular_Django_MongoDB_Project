# ProjectNest Report

## 1. Students And Work Repartition

Project name: **ProjectNest - Personal Knowledge Helper with Isolated Projects**

Students:

| Student | Name | Number | Contribution |
| --- | --- | --- | --- |
| Student 1 | `[Student 1 Name]` | `[Student 1 Number]` | Pair programming on all parts |
| Student 2 | `[Student 2 Name]` | `[Student 2 Number]` | Pair programming on all parts |

We used **pair programming** during the project. Both students contributed together to the frontend, backend, database design, file upload, semantic search, testing, and report preparation. The tasks were not separated strictly by module because we reviewed and implemented the main features together.

## 2. Project Description

ProjectNest is a web application that allows users to create isolated project workspaces. Each project contains its own documents, tags, members, query history, conversations, chunks, and embeddings. The main idea is **project isolation**: when a user opens a project and asks a question, the application searches only inside the files of that selected project.

The site includes:

- User registration, login, logout, and profile update.
- Project creation, update, deletion, search, and ordering.
- File upload for PDF/text documents.
- Image upload for profile images, project cover images, and document thumbnails.
- Project members and tags.
- Semantic assistant using embeddings and a language model.
- Query history and project-scoped search results.

## 3. General Architecture

The project uses three connected layers:

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | Angular | User interface, routing, Reactive Forms, validators, API calls |
| Backend | Django | REST-style API, authentication, validation, file handling, project access control |
| Database | MongoDB Atlas with PyMongo | Stores users, projects, documents, chunks, embeddings, tags, members, and logs |

The Angular frontend communicates with the Django backend through HTTP requests. The Django backend connects to MongoDB Atlas using PyMongo. Uploaded PDFs and images are stored in MongoDB Atlas using GridFS, while normal application metadata is stored in MongoDB collections.

The semantic search architecture is:

1. A user uploads a PDF/text file inside a project.
2. Django stores the document metadata with `project_id`.
3. The backend extracts text from the file.
4. The text is split into chunks.
5. Each chunk receives an embedding vector.
6. Chunks and embeddings are stored with the same `project_id`.
7. When the user asks a question, the query embedding is compared only with embeddings from the selected project.
8. The best matching chunks are sent as context to the LLM to generate a grounded answer.

This prevents data from one project appearing in another project.

## 4. PyMongo With Django

The backend uses Django as the web framework and PyMongo as the MongoDB driver. The MongoDB connection is implemented in `backend/api/db.py` using `MongoClient`. The function `get_db()` returns the selected MongoDB Atlas database, and `ensure_indexes()` creates indexes for important fields such as emails, usernames, project IDs, document IDs, and semantic search records.

PDFs and images are stored with MongoDB GridFS. GridFS is used because MongoDB documents have a size limit, while files can be larger than normal metadata records. The application saves files into the GridFS `fs.files` and `fs.chunks` collections, then stores a reference such as `gridfs:<file_id>` in the related collection.

Because MongoDB is document-based, the project does not define fixed Django ORM model classes. Instead, data is inserted as Python dictionaries. The fields and their types are created implicitly from Python values when the dictionaries are saved to MongoDB.

Example:

- Python `str` values become MongoDB string fields.
- Python `datetime` values become MongoDB date fields.
- MongoDB `ObjectId` values are used as primary keys and reference IDs.
- Lists are used for arrays such as project tag IDs.
- Embedding vectors are stored as arrays of numbers.
- File references are stored as strings pointing to GridFS file IDs.

Even though the schema is flexible, the application still enforces structure through the backend views, serializers, indexes, and access-control functions. For example, every document must have a `project_id`, every chunk must have a `document_id` and `project_id`, and every embedding must have a `chunk_id`, `document_id`, and `project_id`.

## 5. Models / Collections Description

The following MongoDB collections act as the application models.

| Collection | Main Fields | Relationships |
| --- | --- | --- |
| `users` | `_id`, `username`, `email`, `password_hash`, `created_at`, `updated_at` | One user owns many projects |
| `user_profiles` | `_id`, `user_id`, `full_name`, `profile_email`, `joined_date`, `profile_image_path` | One profile belongs to one user |
| `projects` | `_id`, `owner_id`, `owner_email`, `title`, `description`, `visibility_status`, `cover_image_path`, `tag_ids`, `created_at`, `updated_at` | Project belongs to owner; project has documents, members, tags |
| `project_members` | `_id`, `project_id`, `user_id`, `invited_email`, `role`, `added_at` | Links users to projects |
| `tags` | `_id`, `name`, `created_at` | Many-to-many relation with projects through `projects.tag_ids` |
| `documents` | `_id`, `project_id`, `uploaded_by_user_id`, `title`, `document_type`, `file_path`, `thumbnail_image_path`, `uploaded_at`, `extracted_text`, `chunk_count` | Document belongs to one project and one uploader |
| `document_chunks` | `_id`, `document_id`, `project_id`, `chunk_index`, `content`, `created_at` | Chunk belongs to one document and one project |
| `chunk_embeddings` | `_id`, `chunk_id`, `document_id`, `project_id`, `vector`, `model_name`, `created_at` | Embedding belongs to one chunk and one project |
| `semantic_query_logs` | `_id`, `project_id`, `user_id`, `query_text`, `top_k`, `created_at` | Query log belongs to one project and one user |
| `conversations` | `_id`, `project_id`, `user_id`, `title`, `created_at`, `last_updated` | Conversation belongs to one project |
| `messages` | `_id`, `project_id`, `conversation_id`, `sender_type`, `content`, `source_matches`, `created_at` | Message belongs to one conversation |

Assignment field requirements are covered as follows:

- Email fields: `users.email`, `user_profiles.profile_email`, `projects.owner_email`, `project_members.invited_email`.
- Date fields: `created_at`, `updated_at`, `joined_date`, `uploaded_at`, `added_at`, `last_updated`.
- PDF/document file: `documents.file_path`.
- Image file: `user_profiles.profile_image_path`, `projects.cover_image_path`, `documents.thumbnail_image_path`.
- Primary keys: MongoDB `_id`.
- Foreign-key style links: `user_id`, `owner_id`, `project_id`, `document_id`, `chunk_id`, `conversation_id`.
- Many-to-many fields: project tags through `tag_ids`, project collaboration through `project_members`.

## 6. Angular App And Components Structure

The Angular application is organized into `core` services and feature pages.

| Area | Files / Components | Responsibility |
| --- | --- | --- |
| App shell | `app.ts`, `app.html`, `app.routes.ts` | Main layout, navigation, routing |
| Core API | `core/projectnest-api.service.ts` | Sends HTTP requests to Django |
| Core session | `core/session.service.ts` | Stores JWT token, user, and profile in local storage |
| Guards/interceptor | `core/auth.guards.ts`, `core/auth.interceptor.ts` | Protects routes and attaches authentication token |
| Auth pages | `login.page.ts`, `register.page.ts` | Login and register Reactive Forms |
| Profile page | `profile.page.ts` | Edit profile and upload profile image |
| Projects pages | `projects.page.ts`, `project-form.page.ts`, `project-detail.page.ts` | List, search, order, create, update, delete projects |
| Documents page | `document-upload.page.ts` | Upload PDF/text file and optional thumbnail image |
| Assistant page | `assistant.page.ts` | Ask project-scoped semantic questions and show grounded answers |

Angular concepts used:

- Reactive Forms with `FormBuilder`.
- Validators such as `required`, `email`, `minLength`, and `maxLength`.
- Angular Routing with route parameters such as `/projects/:id`.
- Guards for protected routes.
- Services and dependency injection.
- `HttpClient` and Observables for backend communication.

## 7. Frontend Routes

| Route | Page |
| --- | --- |
| `/login` | Login page |
| `/register` | Register page |
| `/profile` | Profile page |
| `/projects` | Project dashboard |
| `/projects/new` | Create project |
| `/projects/:id` | Project details |
| `/projects/:id/edit` | Edit project |
| `/projects/:id/documents/upload` | Upload document |
| `/projects/:id/assistant` | Project assistant |

## 8. Backend URLs

| URL | Methods | Purpose |
| --- | --- | --- |
| `/api/health/` | GET | Check backend and database status |
| `/api/auth/register/` | POST | Register user |
| `/api/auth/login/` | POST | Login user |
| `/api/profile/` | GET, POST/PATCH | Get and update profile |
| `/api/projects/` | GET, POST | List/search/order projects and create project |
| `/api/projects/{project_id}/` | GET, POST/PATCH, DELETE | Project detail, update, delete |
| `/api/projects/{project_id}/members/` | GET, POST | List and add members |
| `/api/projects/{project_id}/members/{member_id}/` | DELETE | Remove member |
| `/api/projects/{project_id}/tags/` | GET, POST | List and add tags |
| `/api/projects/{project_id}/tags/{tag_id}/` | DELETE | Remove tag from project |
| `/api/projects/{project_id}/documents/` | GET, POST | List/search/order documents and upload document |
| `/api/projects/{project_id}/documents/{document_id}/` | GET, PATCH, DELETE | View, update, delete document |
| `/api/projects/{project_id}/semantic-search/` | POST | Ask a project-scoped semantic question |
| `/api/projects/{project_id}/query-history/` | GET | View semantic query history |
| `/api/projects/{project_id}/conversations/` | GET, POST | List/create conversations |
| `/api/projects/{project_id}/conversations/{conversation_id}/` | GET, DELETE | View/delete conversation |
| `/api/projects/{project_id}/conversations/{conversation_id}/messages/` | POST | Add message |
| `/api/files/{file_id}/` | GET | Authenticated file streaming from MongoDB GridFS |

## 9. Testing In The Project

Testing was included at backend, frontend, and manual levels.

Backend verification:

- `python backend/manage.py check` validates Django configuration.
- `python backend/manage.py test api` runs automated tests.

Backend tests cover:

- Text chunking.
- Local embedding vector generation.
- Cosine similarity.
- Grounded answer fallback when there is no context.
- Semantic isolation to prove retrieval filters by selected `project_id`.

Frontend verification:

- `npm run build` checks that the Angular application compiles.
- `npm test -- --watch=false` runs the Angular frontend test setup.

Manual black-box tests:

- Register a user.
- Login and logout.
- Create a project.
- Upload a PDF/text document.
- Upload and view image files.
- Search and order projects.
- Search and order documents.
- Ask a question in one project and confirm that results only come from that project.
- Delete a document and confirm its chunks and embeddings are deleted.

White-box testing focused on the internal isolation rule:

- `rank_project_matches()` queries `chunk_embeddings`, `document_chunks`, and `documents` with the selected `project_id`.
- `_get_accessible_project()` verifies the logged-in user can access the project before data is returned.
- `cascade_delete_document()` removes nested chunks and embeddings.
- `cascade_delete_project()` removes nested project data.

## 10. Conclusion

ProjectNest satisfies the assignment requirements through an Angular frontend, Django backend, and MongoDB Atlas database. The application supports authentication, routing, Reactive Forms, validators, searching, ordering, updating, deleting, file/image upload, document viewing, and linked data. The strongest architectural feature is project isolation: every important record is connected to a project, and all semantic search operations are filtered by `project_id` before returning results or generating an AI answer.
