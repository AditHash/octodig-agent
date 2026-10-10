"""FastAPI transport layer: validation, authentication, and tenant boundaries."""

from __future__ import annotations

import re
from collections.abc import Generator

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_session
from .models import Membership, ResearchEvent, ResearchRun, RunStatus, SellerOffering, StoredReport, TargetAccount, User, Workspace, WorkspaceRole
from .schemas import (
    LoginRequest,
    OfferingCreate,
    OfferingResponse,
    RegisterRequest,
    ResearchRunResponse,
    ResearchStartRequest,
    TargetCreate,
    TargetResponse,
    TokenResponse,
)
from .security import decode_access_token, hash_password, issue_access_token, verify_password
from .settings import get_settings

settings = get_settings()
app = FastAPI(title="OctoDig API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).rstrip("/") for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
bearer = HTTPBearer(auto_error=False)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:72] or "workspace"


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    return user


def active_membership(user: User, session: Session) -> Membership:
    membership = session.scalar(select(Membership).where(Membership.user_id == user.id).limit(1))
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace membership")
    return membership


def require_write_membership(
    user: User = Depends(current_user), session: Session = Depends(get_session)
) -> Membership:
    membership = active_membership(user, session)
    if membership.role == WorkspaceRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access required")
    return membership


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> TokenResponse:
    if session.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    base_slug = slugify(payload.workspace_name)
    workspace_slug = base_slug
    suffix = 2
    while session.scalar(select(Workspace.id).where(Workspace.slug == workspace_slug)):
        workspace_slug = f"{base_slug[:65]}-{suffix}"
        suffix += 1
    user = User(email=payload.email.lower(), name=payload.name.strip(), password_hash=hash_password(payload.password))
    workspace = Workspace(name=payload.workspace_name.strip(), slug=workspace_slug)
    session.add_all([user, workspace])
    session.flush()
    session.add(Membership(user_id=user.id, workspace_id=workspace.id, role=WorkspaceRole.OWNER))
    session.commit()
    return TokenResponse(access_token=issue_access_token(user.id))


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=issue_access_token(user.id))


@app.post("/api/v1/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    payload: TargetCreate,
    membership: Membership = Depends(require_write_membership),
    session: Session = Depends(get_session),
) -> TargetAccount:
    website = str(payload.website) if payload.website else None
    domain = payload.website.host.lower().removeprefix("www.") if payload.website else None
    if domain and session.scalar(
        select(TargetAccount.id).where(
            TargetAccount.workspace_id == membership.workspace_id,
            TargetAccount.normalized_domain == domain,
        )
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target domain already exists")
    target = TargetAccount(
        workspace_id=membership.workspace_id,
        name=payload.name.strip(),
        website=website,
        normalized_domain=domain,
        notes=payload.notes,
        tags=payload.tags,
    )
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


@app.get("/api/v1/targets", response_model=list[TargetResponse])
def list_targets(
    user: User = Depends(current_user), session: Session = Depends(get_session)
) -> list[TargetAccount]:
    membership = active_membership(user, session)
    return list(
        session.scalars(
            select(TargetAccount)
            .where(TargetAccount.workspace_id == membership.workspace_id)
            .order_by(TargetAccount.created_at.desc())
        )
    )


@app.post("/api/v1/offerings", response_model=OfferingResponse, status_code=status.HTTP_201_CREATED)
def create_offering(
    payload: OfferingCreate,
    membership: Membership = Depends(require_write_membership),
    session: Session = Depends(get_session),
) -> SellerOffering:
    base_slug = slugify(payload.name)
    offering_slug = base_slug
    suffix = 2
    while session.scalar(
        select(SellerOffering.id).where(
            SellerOffering.workspace_id == membership.workspace_id, SellerOffering.slug == offering_slug
        )
    ):
        offering_slug = f"{base_slug[:93]}-{suffix}"
        suffix += 1
    offering = SellerOffering(
        workspace_id=membership.workspace_id,
        slug=offering_slug,
        name=payload.name.strip(),
        description=payload.description.strip(),
        capabilities=payload.capabilities,
        business_outcomes=payload.business_outcomes,
        approved=payload.approved,
    )
    session.add(offering)
    session.commit()
    session.refresh(offering)
    return offering


@app.get("/api/v1/offerings", response_model=list[OfferingResponse])
def list_offerings(
    user: User = Depends(current_user), session: Session = Depends(get_session)
) -> list[SellerOffering]:
    membership = active_membership(user, session)
    return list(
        session.scalars(
            select(SellerOffering)
            .where(SellerOffering.workspace_id == membership.workspace_id)
            .order_by(SellerOffering.name)
        )
    )


@app.post(
    "/api/v1/targets/{target_id}/research",
    response_model=ResearchRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_research(
    target_id: str,
    payload: ResearchStartRequest,
    membership: Membership = Depends(require_write_membership),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> ResearchRun:
    target = session.scalar(
        select(TargetAccount).where(
            TargetAccount.id == target_id, TargetAccount.workspace_id == membership.workspace_id
        )
    )
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    run = ResearchRun(
        workspace_id=membership.workspace_id,
        account_id=target.id,
        requested_by_id=user.id,
        provider=payload.provider,
        mode=payload.mode,
        max_cost_usd=str(payload.max_cost_usd),
        input_snapshot={"company_name": target.name, "website": target.website},
    )
    session.add(run)
    session.flush()
    session.add(ResearchEvent(run_id=run.id, event_type="run.queued", data={"provider": run.provider}))
    session.commit()
    session.refresh(run)
    return run


@app.get("/api/v1/runs/{run_id}/report")
def read_report(
    run_id: str, user: User = Depends(current_user), session: Session = Depends(get_session)
) -> dict:
    membership = active_membership(user, session)
    report = session.scalar(
        select(StoredReport).where(StoredReport.run_id == run_id, StoredReport.workspace_id == membership.workspace_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report.payload
