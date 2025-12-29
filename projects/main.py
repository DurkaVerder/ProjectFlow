from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uuid
import httpx
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectMemberAdd, ProjectMemberResponse
from models import Project, ProjectMember
from auth_utils import get_current_user
from config import settings
from kafka_producer import kafka_producer

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await kafka_producer.start()
    yield
    # Shutdown
    await kafka_producer.stop()

app = FastAPI(title="Projects Service", lifespan=lifespan)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


@app.post("/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        ownerId=current_user["id"]
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Отправляем событие в Kafka
    await kafka_producer.send_event('projects-events', {
        'event_type': 'project_created',
        'project_id': str(db_project.id),
        'project_name': db_project.name,
        'owner_id': str(db_project.ownerId)
    })
    
    return ProjectResponse(
        id=str(db_project.id),
        name=db_project.name,
        description=db_project.description,
        status=db_project.status,
        ownerId=str(db_project.ownerId),
        createdAt=db_project.createdAt
    )


@app.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.ownerId == uuid.UUID(current_user["id"])).all()
    
    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            status=p.status,
            ownerId=str(p.ownerId),
            createdAt=p.createdAt
        )
        for p in projects
    ]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status,
        ownerId=str(project.ownerId),
        createdAt=project.createdAt
    )


@app.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if str(project.ownerId) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.status is not None:
        project.status = project_update.status
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status,
        ownerId=str(project.ownerId),
        createdAt=project.createdAt
    )


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if str(project.ownerId) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this project"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@app.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: uuid.UUID,
    member: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if str(project.ownerId) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add members to this project"
        )
    
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.projectId == project_id,
        ProjectMember.userId == uuid.UUID(member.userId)
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )
    
    db_member = ProjectMember(
        projectId=project_id,
        userId=member.userId
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    # Отправляем событие в Kafka
    await kafka_producer.send_event('projects-events', {
        'event_type': 'member_added',
        'project_id': project_id,
        'project_name': project.name,
        'user_id': member.userId
    })
    
    return ProjectMemberResponse(
        id=str(db_member.id),
        projectId=str(db_member.projectId),
        userId=str(db_member.userId),
        addedAt=db_member.addedAt
    )


@app.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
async def get_project_members(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    members = db.query(ProjectMember).filter(ProjectMember.projectId == project_id).all()
    
    # Fetch user names from auth service
    result = []
    async with httpx.AsyncClient() as client:
        for m in members:
            user_name = None
            try:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/auth/users/{m.userId}"
                )
                if response.status_code == 200:
                    user_data = response.json()
                    user_name = user_data.get("name")
            except httpx.RequestError:
                pass
            
            result.append(
                ProjectMemberResponse(
                    id=str(m.id),
                    projectId=str(m.projectId),
                    userId=str(m.userId),
                    userName=user_name,
                    addedAt=m.addedAt
                )
            )
    
    return result


@app.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if str(project.ownerId) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove members from this project"
        )
    
    member = db.query(ProjectMember).filter(
        ProjectMember.projectId == uuid.UUID(project_id),
        ProjectMember.userId == uuid.UUID(user_id)
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this project"
        )
    
    db.delete(member)
    db.commit()
    
    await kafka_producer.send_event('projects-events', {
        'event_type': 'member_removed',
        'project_id': project_id,
        'project_name': project.name,
        'user_id': user_id
    })
    
    return {"message": "Member removed successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
