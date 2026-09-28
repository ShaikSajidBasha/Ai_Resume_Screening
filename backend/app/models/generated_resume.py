from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from app.database.connection import Base


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    original_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    template_name = Column(String(100), nullable=False, default="ATS Professional")
    optimized_content_json = Column(Text, nullable=False)
    optimized_text = Column(Text, nullable=False)
    original_ats_score = Column(Float, nullable=False, default=0)
    optimized_ats_score = Column(Float, nullable=False, default=0)
    original_job_match_score = Column(Float, nullable=False, default=0)
    optimized_job_match_score = Column(Float, nullable=False, default=0)
    original_overall_score = Column(Float, nullable=False, default=0)
    optimized_overall_score = Column(Float, nullable=False, default=0)
    pdf_file_path = Column(String(255), nullable=True)
    docx_file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="generated_resumes")
    analysis = relationship("Analysis", back_populates="generated_resumes")
    original_resume = relationship("Resume", back_populates="generated_resumes")

    __table_args__ = (
        Index("ix_generated_resumes_user_created", "user_id", "created_at"),
        Index("ix_generated_resumes_analysis", "analysis_id"),
    )
