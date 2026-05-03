# ProjectNest Alignment With Doctor Source Material

## Summary

This project now follows the structure and testing style shown in the Doctor's PDFs while keeping the project-specific idea intact: each project is an isolated workspace, and all document chunks, embeddings, assistant answers, query logs, members, and documents stay scoped to one `project_id`.

The implementation intentionally uses Django + PyMongo because `CH7_Django_MongoDB.pdf` presents PyMongo as the recommended option when MongoDB is the primary database. The Angular frontend follows the Doctor's Angular material through services, dependency injection, `HttpClient` Observables, subscriptions, Reactive Forms, validators, and project parameter routing.

## Source Sections Used

| Doctor material | Relevant section | How ProjectNest uses it |
| --- | --- | --- |
| `CH7_Django_MongoDB.pdf` | Introduction, Option 2: Django + PyMongo | Backend uses Django views with `pymongo` collections for MongoDB Atlas instead of forcing Django ORM onto MongoDB. |
| `Angular_CH6_WithDjango.pdf` | API architecture, Django views/URLs, CORS, Angular service using RxJS Observable and `subscribe` | Django exposes `/api/...` routes; Angular calls them through `ProjectNestApiService`; CORS is enabled for Angular dev URLs. |
| `Angular_CH2_ComponentsServicesModules.pdf` | Services and Dependency Injection | API/session logic is separated into injectable services under `frontend/src/app/core`. |
| `Angular_CH4_Forms.pdf` | Reactive Forms, validators | Login, register, profile, project, document upload, member, tag, and assistant forms use `ReactiveFormsModule` with `Validators.required`, `Validators.email`, `Validators.minLength`, and `Validators.maxLength`. |
| `Angular_CH5_Routes.pdf` | Routing, route parameters, `ActivatedRoute.paramMap.subscribe` | Project detail, project edit, document upload, and assistant pages now subscribe to route parameters instead of only reading a snapshot. |
| `CH3_Django_URLsViews.pdf` | URLs, URL conf, views, `JsonResponse` style responses | Backend routes are centralized in `api/urls.py`, included under `/api/`, and views return JSON responses. |
| `CH6_Python_UploadFiles_GenericViews.pdf` | Upload files, file handling, authentication | Profile images, project covers, document files, and document thumbnails are accepted through multipart uploads. |
| `TEST_CH1_TestTechniques.pdf` | V&V, black-box, white-box, unit, integration, system, acceptance, regression testing | The test plan below maps each required test type to ProjectNest scenarios. |
| `TEST_CH2_Postman.pdf` | GET, POST, headers, automated testing, collections, runner | Manual API testing uses Bearer token headers and a repeatable request order. |
| `TEST_CH3_CURL.pdf` | curl GET/POST/PUT/DELETE, headers, upload/download | Command-line API tests are included below for auth, project creation, document upload, and assistant search. |
| `TEST_CH4_JEST.pdf` | Test runner, assertions, mocking, async testing | Frontend test guidance follows Jest-style arrange/act/assert and mocking concepts. The Angular scaffold uses Vitest, but the testing approach is the same. |

## Refactoring Completed

- Route parameter handling was changed to the Doctor's subscription style in these Angular pages:
  - `ProjectDetailPageComponent`
  - `ProjectFormPageComponent`
  - `DocumentUploadPageComponent`
  - `AssistantPageComponent`
- Backend tests were added in `backend/api/tests.py` for:
  - text chunking
  - deterministic local embeddings
  - cosine similarity
  - no-context grounded answer behavior
  - semantic isolation regression proving ranking queries use the selected `project_id`
- The current backend still follows `CH7_Django_MongoDB.pdf` Option 2 because MongoDB Atlas is the primary database for this project.
- The assistant still retrieves chunks by project first, then sends only those selected chunks to the LLM as context.

## Test Plan Based On Doctor Testing PDFs

### Verification and Validation

Verification checks that the app was built correctly:
- Backend system check: `python backend/manage.py check`
- Backend automated tests: `python backend/manage.py test api`
- Frontend build: `npm run build` inside `frontend`

Validation checks that the app solves the assignment problem:
- User can register, login, and edit profile.
- User can create projects and upload files.
- User can ask a question inside Project A and never receive chunks from Project B.
- User can search and order projects/documents.
- User can update and delete records.

### Black-Box Functional Tests

Use these as visible demo tests:
- Register a new user.
- Login and copy the JWT token.
- Create two projects.
- Upload different text/PDF files to each project.
- Ask the same semantic question in both projects.
- Confirm each answer uses only the current project's sources.
- Delete one document and verify its chunks no longer appear in assistant results.

### White-Box Structural Tests

These inspect internal logic:
- Confirm `rank_project_matches()` filters `chunk_embeddings`, `document_chunks`, and `documents` by `project_id`.
- Confirm `Document.project_id`, `DocumentChunk.project_id`, and `ChunkEmbedding.project_id` are consistent.
- Confirm `cascade_delete_document()` removes chunks and embeddings.
- Confirm `cascade_delete_project()` removes documents, chunks, embeddings, query logs, members, and conversations.

### Unit Tests

Current automated unit tests:

```powershell
.\.venv\Scripts\python backend\manage.py test api
```

Covered units:
- `chunk_text`
- `local_hash_embedding`
- `cosine_similarity`
- `generate_grounded_answer`
- `rank_project_matches`

### Integration Tests

Recommended integration flow:
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/projects/`
- `POST /api/projects/{project_id}/documents/`
- `POST /api/projects/{project_id}/semantic-search/`

This validates Angular-Django-MongoDB-OpenRouter integration.

### Regression Tests

Run after every assistant/search change:
- Create Project A with `alpha` content.
- Create Project B with `beta` content.
- Search Project A for terms that strongly match Project B.
- Expected result: Project B never appears.

## Postman Testing Sequence

Create a Postman collection named `ProjectNest API`.

Recommended environment variables:
- `base_url`: `http://127.0.0.1:8000`
- `token`: copied from login response
- `project_id`: copied from project creation response

Requests:

| Name | Method | URL | Headers |
| --- | --- | --- | --- |
| Health | GET | `{{base_url}}/api/health/` | none |
| Register | POST | `{{base_url}}/api/auth/register/` | `Content-Type: application/json` |
| Login | POST | `{{base_url}}/api/auth/login/` | `Content-Type: application/json` |
| List Projects | GET | `{{base_url}}/api/projects/` | `Authorization: Bearer {{token}}` |
| Create Project | POST | `{{base_url}}/api/projects/` | `Authorization: Bearer {{token}}` |
| Upload Document | POST | `{{base_url}}/api/projects/{{project_id}}/documents/` | `Authorization: Bearer {{token}}` |
| Semantic Search | POST | `{{base_url}}/api/projects/{{project_id}}/semantic-search/` | `Authorization: Bearer {{token}}` |

Example semantic search body:

```json
{
  "question": "What does this project say about isolation?",
  "top_k": 5
}
```

Postman automated assertions:

```javascript
pm.test("Status is OK", function () {
  pm.response.to.have.status(200);
});

pm.test("Semantic response is project-scoped", function () {
  const data = pm.response.json();
  pm.expect(data.project_id).to.eql(pm.environment.get("project_id"));
  pm.expect(data.matches).to.be.an("array");
});
```

## curl Testing Examples

Register:

```powershell
curl -X POST http://127.0.0.1:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"username\":\"demo_user\",\"email\":\"demo@example.com\",\"password\":\"Password123\",\"full_name\":\"Demo User\"}"
```

Login:

```powershell
curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"demo@example.com\",\"password\":\"Password123\"}"
```

Create project:

```powershell
curl -X POST http://127.0.0.1:8000/api/projects/ -H "Authorization: Bearer YOUR_TOKEN" -F "title=Course Notes" -F "description=Advanced Web project" -F "visibility_status=private"
```

Upload a document:

```powershell
curl -X POST http://127.0.0.1:8000/api/projects/PROJECT_ID/documents/ -H "Authorization: Bearer YOUR_TOKEN" -F "title=Lecture PDF" -F "document_type=pdf" -F "document=@C:\path\to\lecture.pdf"
```

Run semantic search:

```powershell
curl -X POST http://127.0.0.1:8000/api/projects/PROJECT_ID/semantic-search/ -H "Authorization: Bearer YOUR_TOKEN" -H "Content-Type: application/json" -d "{\"question\":\"What are the main ideas in this project?\",\"top_k\":5}"
```

## Jest-Style Frontend Testing Approach

The Doctor's Jest chapter focuses on a test runner, assertions, mocks, and async code. This Angular project currently uses the Angular 21 default Vitest setup, but the test design should follow the same concepts.

Frontend test cases to add or demonstrate:
- Form validators reject empty login/register values.
- `ProjectNestApiService` calls the correct API URL.
- Assistant page displays `generated_answer` when returned.
- Assistant page displays retrieved snippets below the generated answer.
- Auth guard redirects unauthenticated users to `/login`.

Jest-style structure:

```typescript
describe('AssistantPageComponent', () => {
  it('shows a grounded answer from the API response', async () => {
    // arrange: mock ProjectNestApiService.semanticSearch()
    // act: submit the assistant form
    // assert: expect answer text and snippets to render
  });
});
```

## Demo Script For Presentation

1. Open Angular app and register/login.
2. Create two projects.
3. Upload different PDF/text files into each project.
4. Open Project A assistant and ask a question.
5. Show that the answer includes sources from Project A only.
6. Open Project B and ask a similar question.
7. Show different sources and no data leakage.
8. Use project/document search and ordering controls.
9. Delete a document and explain that chunks and embeddings are also deleted.

## Report Wording

ProjectNest follows a Django + MongoDB architecture using PyMongo, as described in the Doctor's MongoDB chapter. The Angular frontend uses Reactive Forms, validators, routing, route parameters, services, dependency injection, and RxJS Observables as shown in the Angular chapters. Testing follows the Doctor's V&V approach by combining unit tests, integration tests, black-box API tests through Postman/curl, and Jest-style frontend test design.
