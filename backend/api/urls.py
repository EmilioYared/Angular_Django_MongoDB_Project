from django.urls import path

from api import views

urlpatterns = [
    path("health/", views.health),
    path("files/<str:file_id>/", views.file_download),
    path("auth/register/", views.register),
    path("auth/login/", views.login),
    path("profile/", views.profile),
    path("projects/", views.projects),
    path("projects/<str:project_id>/", views.project_detail),
    path("projects/<str:project_id>/members/", views.project_members),
    path("projects/<str:project_id>/members/<str:member_id>/", views.project_member_detail),
    path("projects/<str:project_id>/tags/", views.project_tags),
    path("projects/<str:project_id>/tags/<str:tag_id>/", views.project_tag_detail),
    path("projects/<str:project_id>/documents/", views.documents),
    path("projects/<str:project_id>/documents/<str:document_id>/", views.document_detail),
    path("projects/<str:project_id>/semantic-search/", views.semantic_search),
    path("projects/<str:project_id>/query-history/", views.query_history),
    path("projects/<str:project_id>/conversations/", views.conversations),
    path("projects/<str:project_id>/conversations/<str:conversation_id>/", views.conversation_detail),
    path("projects/<str:project_id>/conversations/<str:conversation_id>/messages/", views.conversation_messages),
]
