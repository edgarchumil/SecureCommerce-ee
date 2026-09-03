from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assets import Asset
from app.models.evaluations import (
    Answer,
    Evaluation,
    EvaluationAsset,
    EvaluationStatus,
    Evidence,
    Framework,
    FrameworkCategory,
    FrameworkControl,
    FrameworkFunction,
    Question,
)
from app.schemas.evaluations import (
    AnswerResponse,
    AnswerUpsert,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationResults,
    EvidenceCreate,
    FrameworkResponse,
    QuestionResponse,
    StatusUpdate,
)
from app.security.dependencies import Principal, get_principal, require_permission
from app.security.permissions import Permission, has_permission
from app.services.audit import add_audit
from app.services.evaluation_scoring import ScoredAnswer, calculate_scores

framework_router = APIRouter(prefix="/frameworks", tags=["marcos"])
router = APIRouter(prefix="/evaluations", tags=["evaluaciones"])


def _org(principal: Principal) -> UUID:
    if principal.organization_id is None:
        raise HTTPException(status_code=403, detail="Seleccione una organización")
    return principal.organization_id


def _response(evaluation: Evaluation) -> EvaluationResponse:
    return EvaluationResponse(
        id=evaluation.id,
        framework_id=evaluation.framework_id,
        code=evaluation.code,
        name=evaluation.name,
        scope=evaluation.scope,
        target_maturity=evaluation.target_maturity,
        status=evaluation.status,
        version=evaluation.version,
        comments=evaluation.comments,
        asset_ids=[item.asset_id for item in evaluation.assets],
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )


async def _evaluation(db: AsyncSession, evaluation_id: UUID, organization_id: UUID) -> Evaluation:
    evaluation = await db.scalar(
        select(Evaluation)
        .options(selectinload(Evaluation.assets))
        .where(
            Evaluation.id == evaluation_id,
            Evaluation.organization_id == organization_id,
            Evaluation.deleted_at.is_(None),
        )
    )
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return evaluation


@framework_router.get("", response_model=list[FrameworkResponse])
async def list_frameworks(
    _: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Framework]:
    return list((await db.scalars(select(Framework).where(Framework.is_active.is_(True)))).all())


@framework_router.get("/{framework_id}/questions", response_model=list[QuestionResponse])
async def list_questions(
    framework_id: UUID,
    _: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[QuestionResponse]:
    rows = (
        await db.execute(
            select(Question, FrameworkControl, FrameworkCategory, FrameworkFunction)
            .join(FrameworkControl, Question.control_id == FrameworkControl.id)
            .join(FrameworkCategory, FrameworkControl.category_id == FrameworkCategory.id)
            .join(FrameworkFunction, FrameworkCategory.function_id == FrameworkFunction.id)
            .where(FrameworkFunction.framework_id == framework_id, Question.is_active.is_(True))
            .order_by(
                FrameworkFunction.sort_order, FrameworkCategory.sort_order, Question.sort_order
            )
        )
    ).all()
    return [
        QuestionResponse(
            id=question.id,
            function_code=function.code,
            function_name=function.name,
            category_code=category.code,
            category_name=category.name,
            control_code=control.code,
            text=question.text,
            help_text=question.help_text,
            weight=question.weight,
            expected_evidence=question.expected_evidence,
            response_options=question.response_options,
            base_recommendation=question.base_recommendation,
        )
        for question, control, category, function in rows
    ]


@router.get("", response_model=list[EvaluationResponse])
async def list_evaluations(
    principal: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[EvaluationResponse]:
    evaluations = (
        await db.scalars(
            select(Evaluation)
            .options(selectinload(Evaluation.assets))
            .where(Evaluation.organization_id == _org(principal), Evaluation.deleted_at.is_(None))
            .order_by(Evaluation.updated_at.desc())
        )
    ).all()
    return [_response(item) for item in evaluations]


@router.post("", response_model=EvaluationResponse, status_code=201)
async def create_evaluation(
    payload: EvaluationCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    organization_id = _org(principal)
    framework = await db.scalar(
        select(Framework).where(Framework.id == payload.framework_id, Framework.is_active.is_(True))
    )
    if framework is None:
        raise HTTPException(status_code=422, detail="Marco no válido")
    asset_ids = list(dict.fromkeys(payload.asset_ids))
    found = (
        set(
            (
                await db.scalars(
                    select(Asset.id).where(
                        Asset.id.in_(asset_ids),
                        Asset.organization_id == organization_id,
                        Asset.deleted_at.is_(None),
                    )
                )
            ).all()
        )
        if asset_ids
        else set()
    )
    if found != set(asset_ids):
        raise HTTPException(status_code=422, detail="Uno o más activos no son válidos")
    duplicate = await db.scalar(
        select(Evaluation.id).where(
            Evaluation.organization_id == organization_id,
            Evaluation.code == payload.code,
            Evaluation.version == 1,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="El código de evaluación ya existe")
    evaluation = Evaluation(
        organization_id=organization_id,
        created_by=principal.user.id,
        framework_id=payload.framework_id,
        code=payload.code,
        name=payload.name,
        scope=payload.scope,
        target_maturity=payload.target_maturity,
        comments=payload.comments,
        assets=[],
    )
    db.add(evaluation)
    await db.flush()
    evaluation.assets.extend(
        EvaluationAsset(
            organization_id=organization_id, evaluation_id=evaluation.id, asset_id=asset_id
        )
        for asset_id in asset_ids
    )
    add_audit(
        db,
        request,
        "evaluation.create",
        "evaluation",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(evaluation.id),
    )
    await db.commit()
    return _response(evaluation)


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    return _response(await _evaluation(db, evaluation_id, _org(principal)))


@router.post("/{evaluation_id}/versions", response_model=EvaluationResponse, status_code=201)
async def create_version(
    evaluation_id: UUID,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    organization_id = _org(principal)
    source = await _evaluation(db, evaluation_id, organization_id)
    latest = await db.scalar(
        select(Evaluation.version)
        .where(
            Evaluation.organization_id == organization_id,
            Evaluation.code == source.code,
        )
        .order_by(Evaluation.version.desc())
        .limit(1)
    )
    version = (latest or 0) + 1
    evaluation = Evaluation(
        organization_id=organization_id,
        created_by=principal.user.id,
        framework_id=source.framework_id,
        code=source.code,
        name=source.name,
        scope=source.scope,
        target_maturity=source.target_maturity,
        comments=source.comments,
        version=version,
        assets=[],
    )
    db.add(evaluation)
    await db.flush()
    evaluation.assets.extend(
        EvaluationAsset(
            organization_id=organization_id,
            evaluation_id=evaluation.id,
            asset_id=item.asset_id,
        )
        for item in source.assets
    )
    add_audit(
        db,
        request,
        "evaluation.version.create",
        "evaluation",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(evaluation.id),
        changes={"source_id": str(source.id), "version": version},
    )
    await db.commit()
    return _response(evaluation)


@router.get("/{evaluation_id}/answers", response_model=list[AnswerResponse])
async def list_answers(
    evaluation_id: UUID,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Answer]:
    organization_id = _org(principal)
    await _evaluation(db, evaluation_id, organization_id)
    return list(
        (
            await db.scalars(
                select(Answer).where(
                    Answer.evaluation_id == evaluation_id, Answer.organization_id == organization_id
                )
            )
        ).all()
    )


@router.put("/{evaluation_id}/answers/{question_id}", response_model=AnswerResponse)
async def save_answer(
    evaluation_id: UUID,
    question_id: UUID,
    payload: AnswerUpsert,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_ANSWER)),
    db: AsyncSession = Depends(get_db),
) -> Answer:
    organization_id = _org(principal)
    evaluation = await _evaluation(db, evaluation_id, organization_id)
    if evaluation.status not in (EvaluationStatus.DRAFT, EvaluationStatus.IN_REVIEW):
        raise HTTPException(status_code=409, detail="La evaluación ya no admite cambios")
    valid_question = await db.scalar(
        select(Question.id)
        .join(FrameworkControl)
        .join(FrameworkCategory)
        .join(FrameworkFunction)
        .where(
            Question.id == question_id, FrameworkFunction.framework_id == evaluation.framework_id
        )
    )
    if valid_question is None:
        raise HTTPException(status_code=422, detail="Pregunta no válida")
    answer = await db.scalar(
        select(Answer).where(
            Answer.evaluation_id == evaluation_id, Answer.question_id == question_id
        )
    )
    if answer is None:
        answer = Answer(
            organization_id=organization_id,
            evaluation_id=evaluation_id,
            question_id=question_id,
            answered_by=principal.user.id,
            maturity=payload.maturity,
            comment=payload.comment,
        )
        db.add(answer)
    else:
        answer.maturity = payload.maturity
        answer.comment = payload.comment
        answer.answered_by = principal.user.id
    add_audit(
        db,
        request,
        "evaluation.answer.save",
        "answer",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(answer.id),
    )
    await db.commit()
    return answer


@router.post("/{evaluation_id}/answers/{question_id}/evidence", status_code=201)
async def add_evidence(
    evaluation_id: UUID,
    question_id: UUID,
    payload: EvidenceCreate,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_ANSWER)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    organization_id = _org(principal)
    await _evaluation(db, evaluation_id, organization_id)
    answer = await db.scalar(
        select(Answer).where(
            Answer.evaluation_id == evaluation_id,
            Answer.question_id == question_id,
            Answer.organization_id == organization_id,
        )
    )
    if answer is None:
        raise HTTPException(
            status_code=409, detail="Guarde una respuesta antes de agregar evidencia"
        )
    evidence = Evidence(
        organization_id=organization_id,
        answer_id=answer.id,
        uploaded_by=principal.user.id,
        storage_key=f"{organization_id}/evidence/{uuid4()}",
        **payload.model_dump(),
    )
    db.add(evidence)
    await db.flush()
    add_audit(
        db,
        request,
        "evaluation.evidence.add",
        "evidence",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(evidence.id),
        changes={"file_name": evidence.file_name, "sha256": evidence.sha256},
    )
    await db.commit()
    return {"id": str(evidence.id), "status": "registered"}


@router.patch("/{evaluation_id}/status", response_model=EvaluationResponse)
async def update_status(
    evaluation_id: UUID,
    payload: StatusUpdate,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    organization_id = _org(principal)
    evaluation = await _evaluation(db, evaluation_id, organization_id)
    allowed = {
        EvaluationStatus.DRAFT: EvaluationStatus.IN_REVIEW,
        EvaluationStatus.IN_REVIEW: EvaluationStatus.APPROVED,
        EvaluationStatus.APPROVED: EvaluationStatus.CLOSED,
    }
    if allowed.get(EvaluationStatus(evaluation.status)) != payload.status:
        raise HTTPException(status_code=409, detail="Transición de estado no permitida")
    permission = (
        Permission.EVALUATION_ANSWER
        if payload.status == EvaluationStatus.IN_REVIEW
        else Permission.EVALUATION_REVIEW
    )
    if principal.role is None or not has_permission(principal.role, permission):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    evaluation.status = payload.status
    add_audit(
        db,
        request,
        "evaluation.status.update",
        "evaluation",
        "success",
        user_id=principal.user.id,
        organization_id=organization_id,
        resource_id=str(evaluation.id),
        changes={"status": payload.status.value},
    )
    await db.commit()
    return _response(evaluation)


@router.get("/{evaluation_id}/results", response_model=EvaluationResults)
async def results(
    evaluation_id: UUID,
    principal: Principal = Depends(require_permission(Permission.EVALUATION_READ)),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResults:
    organization_id = _org(principal)
    evaluation = await _evaluation(db, evaluation_id, organization_id)
    rows = (
        await db.execute(
            select(Question, FrameworkCategory, FrameworkFunction, Answer)
            .join(FrameworkControl, Question.control_id == FrameworkControl.id)
            .join(FrameworkCategory, FrameworkControl.category_id == FrameworkCategory.id)
            .join(FrameworkFunction, FrameworkCategory.function_id == FrameworkFunction.id)
            .outerjoin(
                Answer,
                (Answer.question_id == Question.id)
                & (Answer.evaluation_id == evaluation.id)
                & (Answer.organization_id == organization_id),
            )
            .where(
                FrameworkFunction.framework_id == evaluation.framework_id,
                Question.is_active.is_(True),
            )
            .order_by(FrameworkFunction.sort_order, FrameworkCategory.sort_order)
        )
    ).all()
    scored = [
        ScoredAnswer(
            function.code,
            function.name,
            category.code,
            category.name,
            question.weight,
            answer.maturity if answer else None,
        )
        for question, category, function, answer in rows
    ]
    return EvaluationResults.model_validate(calculate_scores(scored, evaluation.target_maturity))
