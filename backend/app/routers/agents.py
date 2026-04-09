"""
智能体和技能管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Agent, Skill

router = APIRouter()


# ============== Schemas ==============

class SkillResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    icon: str
    skill_type: str
    capabilities: list
    system_prompt_fragment: Optional[str]

    class Config:
        from_attributes = True


class AgentSkillInfo(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    icon: str


class AgentResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    is_builtin: bool
    is_active: bool
    persona_system_prompt: Optional[str]
    thinking_style: Optional[str]
    output_format: Optional[str]
    output_verbosity: Optional[str]
    skills: List[AgentSkillInfo]

    class Config:
        from_attributes = True


class CreateAgentRequest(BaseModel):
    name: str
    description: Optional[str] = None
    skill_ids: List[str]
    persona_system_prompt: Optional[str] = None


# ============== Skill APIs ==============

@router.get("/skills", response_model=List[SkillResponse])
def list_skills(db: Session = Depends(get_db)):
    """获取所有技能列表"""
    skills = db.query(Skill).filter(Skill.is_active == True).all()
    return skills


@router.get("/skills/{skill_id}", response_model=SkillResponse)
def get_skill(skill_id: str, db: Session = Depends(get_db)):
    """获取技能详情"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


# ============== Agent APIs ==============

@router.get("/agents", response_model=List[AgentResponse])
def list_agents(
    builtin_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取智能体列表"""
    query = db.query(Agent).filter(Agent.is_active == True)
    if builtin_only:
        query = query.filter(Agent.is_builtin == True)
    agents = query.all()
    return agents


@router.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """获取智能体详情"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return agent


@router.post("/agents", response_model=AgentResponse)
def create_agent(
    req: CreateAgentRequest,
    db: Session = Depends(get_db)
):
    """创建自定义智能体"""
    import json
    import uuid
    from datetime import datetime

    # 生成唯一 code
    code = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 创建智能体
    agent = Agent(
        id=str(uuid.uuid4()),
        code=code,
        name=req.name,
        description=req.description,
        is_builtin=False,
        is_active=True,
        persona_system_prompt=req.persona_system_prompt,
        persona_expertise=json.dumps([]),
        output_verbosity="concise",
        visualization_preferences=json.dumps(["table"]),
        data_scope={}
    )

    # 关联技能
    for skill_id in req.skill_ids:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if skill:
            agent.skills.append(skill)

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """删除自定义智能体"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")

    if agent.is_builtin:
        raise HTTPException(status_code=400, detail="不能删除内置智能体")

    agent.is_active = False
    db.commit()

    return {"success": True, "message": "智能体已删除"}
