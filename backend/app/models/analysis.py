from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)

    ats_score = Column(Float, nullable=False, default=0)
    job_match_score = Column(Float, nullable=False, default=0)
    skill_score = Column(Float, nullable=False, default=0)
    keyword_score = Column(Float, nullable=False, default=0)
    experience_score = Column(Float, nullable=False, default=0)
    education_score = Column(Float, nullable=False, default=0)
    resume_quality_score = Column(Float, nullable=False, default=0)
    overall_score = Column(Float, nullable=False, default=0)

    recommendation = Column(Text, nullable=True)  # final_summary text
    status = Column(String(50), nullable=True)    # Strong Match / Moderate Match / ...
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")
    job_description = relationship("JobDescription", back_populates="analyses")
    extracted_skills = relationship("ExtractedSkill", back_populates="analysis", cascade="all, delete-orphan")
    missing_keywords = relationship("MissingKeyword", back_populates="analysis", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="analysis", cascade="all, delete-orphan")
    agent_results = relationship("AgentResult", back_populates="analysis", cascade="all, delete-orphan")
    generated_resumes = relationship("GeneratedResume", back_populates="analysis", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_analyses_user_created", "user_id", "created_at"),
    )


class ExtractedSkill(Base):
    __tablename__ = "extracted_skills"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(150), nullable=False)
    skill_type = Column(String(50), nullable=True)  # Programming/Framework/Database/Cloud/AI-ML/Tool/Soft/Domain
    present_in_resume = Column(Integer, default=0)  # 0/1 boolean
    required_by_job = Column(Integer, default=0)    # 0/1 boolean

    analysis = relationship("Analysis", back_populates="extracted_skills")


class MissingKeyword(Base):
    __tablename__ = "missing_keywords"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(150), nullable=False)
    importance = Column(String(20), nullable=False, default="Medium")  # High/Medium/Low

    analysis = relationship("Analysis", back_populates="missing_keywords")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    recommendation = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="MEDIUM")  # HIGH/MEDIUM/LOW

    analysis = relationship("Analysis", back_populates="recommendations")
