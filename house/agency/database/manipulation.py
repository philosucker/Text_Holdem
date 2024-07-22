from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Agent
from utils import nick_name_generator, stk_size_generator

class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    # from_dealer
    async def get_available_agents_by_difficulty(self, data: dict[str, int]) -> dict[str, int]:
        agents = dict()
        for difficulty, count in data.items():
            result = await self.session.execute(select(Agent).filter(Agent.difficulty == difficulty, Agent.available == "yes"))
            available_agents = result.scalars().all()

            if len(available_agents) < count:
                for _ in range(count - len(available_agents)):
                    nick_name = nick_name_generator()
                    stack_size = stk_size_generator(difficulty)
                    agent = await self._create_agent(nick_name, stack_size, difficulty)
                    agents[agent.nick_name] = agent.stack_size
            
            for agent in available_agents:
                agent.available = 'no'
                agents[agent.nick_name] = agent.stack_size
            
            await self._update_agent_availability([agent.id for agent in available_agents], "no")

        return agents

    async def _create_agent(self, nick_name: str, stack_size: int, difficulty: str) -> Agent:
        agent = Agent(nick_name=nick_name, stack_size=stack_size, difficulty=difficulty, available="no")
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def _update_agent_availability(self, agent_ids: list[int], availability: str):
        await self.session.execute(
            select(Agent).filter(Agent.id.in_(agent_ids)).update({Agent.available: availability}, synchronize_session=False)
        )
        await self.session.commit()

    # from_floor
    async def update_agents_stack_size(self, data: dict[int, int]) -> list[Agent]:
        agent_ids = list(data.keys())
        result = await self.session.execute(select(Agent).filter(Agent.id.in_(agent_ids)))
        agents = result.scalars().all() # 조건에 맞는 agent 객체들을 list에 담는다

        for agent in agents:
            if agent.id in data:
                agent.stack_size = data[agent.id]

        await self.session.commit()
        return agents
    
