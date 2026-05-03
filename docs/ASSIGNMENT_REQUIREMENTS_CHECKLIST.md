# ProjectNest Assignment Requirements Checklist

This checklist covers the implemented requirements except the explicit Mongoose/class-model part, which this project handles with Django + PyMongo + MongoDB Atlas collections.

## Backend And Database

| Requirement | Status | Evidence |
| --- | --- | --- |
| Django backend | Implemented | `backend/api/views.py`, `backend/api/urls.py` |
| MongoDB database | Implemented | `backend/api/db.py` connects with PyMongo and creates indexes |
| Primary keys | Implemented | MongoDB `_id` values are used as primary identifiers |
| Foreign-key style links | Implemented | `user_id`, `owner_id`, `project_id`, `document_id`, `chunk_id`, `conversation_id` |
| Many-to-many style relation | Implemented | project tags through `projects.tag_ids`; project users through `project_members` |
| Email fields | Implemented | users, profiles, projects, project members |
| Date fields | Implemented | `created_at`, `updated_at`, `joined_date`, `uploaded_at`, `added_at`, `last_updated` |
| PDF/document file | Implemented | `documents.file_path` stores a GridFS reference; document upload endpoint |
| Image file | Implemented | profile image, project cover image, document thumbnail image stored in GridFS |

## Website Features

| Requirement | Status | Evidence |
| --- | --- | --- |
| User authentication | Implemented | register, login, logout, auth guard, profile |
| Retrieve data | Implemented | project, document, member, tag, query-history endpoints and UI |
| Search by criteria | Implemented | project title search, document title search, semantic project search |
| Ordering data | Implemented | projects by date/title, documents by upload date/title |
| Updating data | Implemented | profile update, project update, document update endpoint |
| Deleting data | Implemented | project, document, member, and tag delete |
| Link between tables | Implemented | ObjectId references and project-scoped access checks |
| Link between pages | Implemented | Angular routes from dashboard to project, edit, upload, assistant, profile |
| Upload image | Implemented | profile image, project cover image, document thumbnail stored in MongoDB Atlas GridFS |
| View uploaded image | Implemented | profile preview, project cover preview, document thumbnail preview |
| Upload document | Implemented | project document upload supports PDF/text files stored in MongoDB Atlas GridFS |
| View attached document | Implemented | document list exposes an `Open file` link |

## Angular Concepts

| Requirement | Status | Evidence |
| --- | --- | --- |
| Angular validators | Implemented | required, email, minLength, maxLength validators |
| Reactive Forms | Implemented | login, register, profile, project, document, member, tag, assistant forms |
| Angular Routing | Implemented | `frontend/src/app/app.routes.ts` and route-param pages |
| Link between pages | Implemented | `routerLink`, auth guards, project-scoped routes |

## Project Isolation Requirement

All semantic retrieval is project-scoped:

- Documents are stored with `project_id`.
- Document and image files are stored in GridFS with access metadata.
- Chunks are stored with `document_id` and `project_id`.
- Embeddings are stored with `chunk_id`, `document_id`, and `project_id`.
- Semantic search filters embeddings, chunks, and documents by the selected `project_id`.
- Project deletion cascades documents, chunks, embeddings, conversations, members, and query logs.

The main isolation logic is implemented in `backend/api/semantic.py` and enforced through `_get_accessible_project()` in `backend/api/views.py`.
