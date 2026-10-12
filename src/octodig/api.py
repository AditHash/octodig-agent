"""FastAPI transport layer: validation, authentication, and tenant boundaries."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Generator
from datetime import UTC, datetime

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal, get_session
from .models import Membership, ResearchEvent, ResearchRun, RunStatus, SellerOffering, StoredReport, TargetAccount, User, Workspace, WorkspaceRole
from .schemas import (
    LoginRequest,
    OfferingCreate,
    OfferingResponse,
    RegisterRequest,
    ResearchRunResponse,
    ResearchRunStatusResponse,
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


def time_now_utc() -> datetime:
    return datetime.now(UTC)


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
    """Compatibility liveness endpoint for load balancers."""
    return {"status": "ok"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


def database_ready(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


@app.get("/health/ready")
def readiness(session: Session = Depends(get_session)) -> dict[str, str]:
    if not database_ready(session):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return {"status": "ready"}


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
    idempotency_key: str | None = Header(default=None, max_length=80),
    membership: Membership = Depends(require_write_membership),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> ResearchRun:
    if idempotency_key is not None and not re.fullmatch(r"[A-Za-z0-9_-]+", idempotency_key):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Idempotency-Key")
    existing = None
    if idempotency_key is not None:
        existing = session.scalar(select(ResearchRun).where(
            ResearchRun.workspace_id == membership.workspace_id,
            ResearchRun.idempotency_key == idempotency_key,
        ))
        if existing is not None:
            if not same_research_request(existing, target_id, payload):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency key was used for a different request")
            return existing
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
        idempotency_key=idempotency_key,
        input_snapshot={"company_name": target.name, "website": target.website},
    )
    session.add(run)
    session.flush()
    session.add(ResearchEvent(run_id=run.id, event_type="run.queued", data={"provider": run.provider}))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(ResearchRun).where(
            ResearchRun.workspace_id == membership.workspace_id,
            ResearchRun.idempotency_key == idempotency_key,
        ))
        if existing is not None and same_research_request(existing, target_id, payload):
            return existing
        raise
    session.refresh(run)
    return run


def same_research_request(run: ResearchRun, target_id: str, payload: ResearchStartRequest) -> bool:
    return (
        run.account_id == target_id
        and run.provider == payload.provider
        and run.mode == payload.mode
        and run.max_cost_usd == str(payload.max_cost_usd)
    )


def _owned_run(session: Session, run_id: str, workspace_id: str) -> ResearchRun:
    run = session.scalar(select(ResearchRun).where(ResearchRun.id == run_id, ResearchRun.workspace_id == workspace_id))
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    return run


@app.get("/api/v1/runs/{run_id}", response_model=ResearchRunStatusResponse)
def read_run_status(
    run_id: str, user: User = Depends(current_user), session: Session = Depends(get_session)
) -> ResearchRun:
    return _owned_run(session, run_id, active_membership(user, session).workspace_id)


@app.post("/api/v1/runs/{run_id}/cancel", response_model=ResearchRunStatusResponse)
def cancel_run(
    run_id: str,
    membership: Membership = Depends(require_write_membership),
    session: Session = Depends(get_session),
) -> ResearchRun:
    run = _owned_run(session, run_id, membership.workspace_id)
    if run.status == RunStatus.QUEUED:
        run.status = RunStatus.CANCELLED
        run.ended_at = time_now_utc()
        session.add(ResearchEvent(run_id=run.id, event_type="run.cancelled", data={"before_start": True}))
    elif run.status in {RunStatus.RESEARCHING, RunStatus.NORMALIZING, RunStatus.MATCHING, RunStatus.RENDERING}:
        run.status = RunStatus.CANCEL_REQUESTED
        session.add(ResearchEvent(run_id=run.id, event_type="run.cancel_requested", data={}))
    session.commit()
    session.refresh(run)
    return run


def _sse(event: ResearchEvent) -> str:
    return f"id: {event.id}\nevent: {event.event_type}\ndata: {json.dumps(event.data, separators=(',', ':'))}\n\n"


@app.get("/api/v1/runs/{run_id}/events")
def stream_run_events(
    run_id: str,
    after: str | None = Query(default=None, max_length=80),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> StreamingResponse:
    workspace_id = active_membership(user, session).workspace_id
    _owned_run(session, run_id, workspace_id)

    def event_stream():
        seen = after
        for _ in range(30):
            with SessionLocal() as event_session:
                run = _owned_run(event_session, run_id, workspace_id)
                events = list(event_session.scalars(
                    select(ResearchEvent).where(ResearchEvent.run_id == run_id).order_by(ResearchEvent.created_at, ResearchEvent.id)
                ))
                if seen:
                    indexes = [index for index, item in enumerate(events) if item.id == seen]
                    events = events[indexes[-1] + 1:] if indexes else events
                for event in events:
                    seen = event.id
                    yield _sse(event)
                if run.status in {RunStatus.COMPLETED, RunStatus.COMPLETED_PARTIAL, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.BUDGET_EXCEEDED}:
                    return
            yield ": keepalive\n\n"
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


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


@app.get("/api/v1/runs/{run_id}/report.md", response_class=PlainTextResponse)
def read_report_markdown(
    run_id: str, user: User = Depends(current_user), session: Session = Depends(get_session)
) -> str:
    membership = active_membership(user, session)
    report = session.scalar(
        select(StoredReport).where(StoredReport.run_id == run_id, StoredReport.workspace_id == membership.workspace_id)
    )
    if report is None or report.markdown is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Markdown report not found")
    return report.markdown
