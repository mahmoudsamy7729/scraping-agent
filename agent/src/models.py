from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class AgentRunStatus(str, enum.Enum):
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"


class AgentRunToolStatus(str, enum.Enum):
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(
            AgentStatus,
            name="agent_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=AgentStatus.ACTIVE,
        server_default=AgentStatus.ACTIVE.value,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    runs: Mapped[list[AgentRun]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(
            AgentRunStatus,
            name="agent_run_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=AgentRunStatus.STARTED,
        server_default=AgentRunStatus.STARTED.value,
    )
    input_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    tools: Mapped[list[AgentRunTool]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )

    agent: Mapped[Agent] = relationship(back_populates="runs")


class AgentRunTool(Base):
    __tablename__ = "agent_run_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    call_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AgentRunToolStatus] = mapped_column(
        Enum(
            AgentRunToolStatus,
            name="agent_run_tool_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=AgentRunToolStatus.STARTED,
        server_default=AgentRunToolStatus.STARTED.value,
    )
    tool_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    run: Mapped[AgentRun] = relationship(back_populates="tools")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list["ScrapedDocument"]] = relationship(
        back_populates="scrape_run",
        cascade="all, delete-orphan",
    )


class ScrapedDocument(Base):
    __tablename__ = "scraped_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scrape_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scrape_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scrape_run: Mapped["ScrapeRun"] = relationship(back_populates="documents")
    processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    extracted_entities: Mapped[list["ExtractedEntity"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scraped_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["ScrapedDocument"] = relationship(back_populates="processing_tasks")


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scraped_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    structured_data: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    extracted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    document: Mapped["ScrapedDocument"] = relationship(back_populates="extracted_entities")
