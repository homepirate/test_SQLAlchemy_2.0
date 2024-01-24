import random

from database import async_engine, Base, async_session
import asyncio
from sqlalchemy import select, func, cast, Integer, and_, insert
from sqlalchemy.orm import aliased, selectinload, contains_eager, joinedload

from dtos import WorkerDTO, WorkerRelDTO
from models import Worker, Resume, Workload, Vacancy


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_workers():
    names = [
        "Artem",
        "Roman",
        "Petr",
        "Jack",
        "Nik"
    ]
    workers = [Worker(username=name) for name in names]
    async with async_session() as session:
        session.add_all(workers)
        await session.commit()


async def select_workers():
    async with async_session() as session:
        res = await session.execute(select(Worker))
        print(res.scalars().all())


async def update_workers():
    async with async_session() as session:
        res = await session.execute(select(Worker))
        first_worker = res.scalars().all()[0]
        first_worker.username = "BRO"
        await session.commit()

        # здесь будет сделано два запроса 1 - на поиск объекта
        # 2 - на изменение, можно использовать update().values().filter_by() (или .where())
        # тогда будет выполнен только один запрос

        # session.expire_all() - сбросит все сделанные изменения
        # session.refresh(some_obj) - обновит объект до текущего состояния в БД(сделает к ней запрос)


async def insert_resumes():
    async with async_session() as session:

        res = await session.execute(select(Worker))
        res = res.scalars().all()


        # 1 способ добавления
        resume_jack_1 = Resume(
            title="Python Junior Developer", compensation=50000, workload=Workload.fulltime, worker_id=random.choice(res).id)
        resume_jack_2 = Resume(
            title="Python Разработчик", compensation=150000, workload=Workload.fulltime, worker_id=random.choice(res).id)
        resume_michael_1 = Resume(
            title="Python Data Engineer", compensation=250000, workload=Workload.parttime, worker_id=random.choice(res).id)
        resume_michael_2 = Resume(
            title="Data Scientist", compensation=300000, workload=Workload.fulltime, worker_id=random.choice(res).id)
        session.add_all([resume_jack_1, resume_jack_2,
                         resume_michael_1, resume_michael_2])

        await session.flush()

        # 2 способ добавления
        resumes = [
            {"title": "Python программист", "compensation": 60000, "workload": "fulltime",
             "worker_id": random.choice(res).id},
            {"title": "Machine Learning Engineer", "compensation": 70000, "workload": "parttime",
             "worker_id": random.choice(res).id},
            {"title": "Python Data Scientist", "compensation": 80000, "workload": "parttime",
             "worker_id": random.choice(res).id},
            {"title": "Python Analyst", "compensation": 90000, "workload": "fulltime",
             "worker_id": random.choice(res).id},
            {"title": "Python Junior Developer", "compensation": 100000, "workload": "fulltime",
             "worker_id": random.choice(res).id},
        ]

        insert_resumes = insert(Resume).values(resumes)
        await session.execute(insert_resumes)
        await session.commit()


async def select_resumes_avg_compensation(like_language: str = "Python", salary: int = 40000):
    """
            select workload, avg(compensation)::int as avg_compensation
            from resumes
            where title like '%Python%' and compensation > 40000
            group by workload
    """
    async with async_session() as session:
        query = (
            select(Resume.workload, cast(func.avg(Resume.compensation), Integer).label("avg_compensation")
                   ).filter(and_(Resume.title.contains(like_language),
                                 Resume.compensation > salary,
                                 )).group_by(Resume.workload)
        )
        print(query.compile(compile_kwargs={"literal_binds": True})) # просто выведет наш запрос с подставленными значениями
        result = await session.execute(query)
        result = result.all()
        print(result)
        print(result[0].avg_compensation) # можно обращаться по имени, которое передали в label


async def join_cte_subquery_window_func():
    """
    WITH helper2 AS (
        SELECT *, compensation-avg_workload_compensation AS compensation_diff
        FROM
        (SELECT
            w.id,
            w.username,
            r.compensation,
            r.workload,
            avg(r.compensation) OVER (PARTITION BY workload)::int AS avg_workload_compensation
        FROM resumes r
        JOIN workers w ON r.worker_id = w.id) helper1
    )
    SELECT * FROM helper2
    ORDER BY compensation_diff DESC;
    """
    async with async_session() as session:
        r = aliased(Resume)
        w = aliased(Worker)
        subq = (
            select(r, w, func.avg(r.compensation).over(partition_by=r.workload).cast(Integer).label("avg_workload_compensation"))
            .join(r, r.worker_id == w.id)
        ).subquery("helper1") # даем название
        cte = (
            select(
                subq.c.worker_id,
                subq.c.username,
                subq.c.compensation,
                subq.c.workload,
                subq.c.avg_workload_compensation,
                (subq.c.compensation - subq.c.avg_workload_compensation).label("compensation_diff")
            )
        ).cte("helper2") # даем название
        query = (
            select(cte).order_by(cte.c.compensation_diff.desc())
        )

        print(query.compile(compile_kwargs={"literal_binds": True}))
        result = await session.execute(query)
        print(result.all())


async def select_workers_with_condition_relationship():
    async with async_session() as session:
        result = await session.execute(select(Worker).options(selectinload(Worker.resumes_parttime)))
        result = result.scalars().all()
        print(result)


async def select_workers_with_condition_relationship_contains_eager():
    async with async_session() as session:
        result = await session.execute(select(Worker)
                                       .join(Worker.resumes)
                                       .options(contains_eager(Worker.resumes))
                                       .filter(Resume.workload == 'parttime'))
        print(result.unique().scalars().all())


async def select_workers_with_relationship_contains_eager_with_limit():
    async with async_session() as session:
        subq = select(Resume.id.label("parrtime_resume_id")
                      ).filter(Resume.worker_id == Worker.id
                               ).order_by(Worker.id.desc()).limit(2).scalar_subquery().correlate(Worker) # scalar_subquery вернет не кортеж, а только одно значение

        query = select(Worker).join(Resume, Resume.id.in_(subq)).options(contains_eager(Worker.resumes))

        result = await session.execute(query)
        print(result.unique().scalars().all())


async def get_dtos_mapp():
    async with async_session() as session:
        result = await session.execute(select(Worker).limit(2))
        result = result.scalars().all()
        result_dtos = [WorkerDTO.model_validate(row, from_attributes=True) for row in result]
        print(result_dtos)


async def get_dtos_mapp_with_relationship():
    async with async_session() as session:
        result = await session.execute(select(Worker).options(selectinload(Worker.resumes)).limit(2))
        result = result.scalars().all()
        result_dtos = [WorkerRelDTO.model_validate(row, from_attributes=True) for row in result]
        print(result_dtos)
        return result_dtos


async def add_vacancies_replies():
    async with async_session() as session:
        resumes = await session.execute(select(Resume))
        resumes = resumes.scalars().all()
        new_vacancy = Vacancy(title="Python разработчик", compensation=100000)
        get_resume_1 = select(Resume).options(selectinload(Resume.vacancies_replied)).filter_by(id=random.choice(resumes).id)
        get_resume_2 = select(Resume).options(selectinload(Resume.vacancies_replied)).filter_by(id=random.choice(resumes).id)
        resume_1 = (await session.execute(get_resume_1)).scalar_one()
        resume_2 = (await session.execute(get_resume_2)).scalar_one()
        resume_1.vacancies_replied.append(new_vacancy)
        resume_2.vacancies_replied.append(new_vacancy)
        await session.commit()


async def select_resumes_with_all_relationships():
    async with async_session() as session:
        query = (select(Resume)
                 .options(joinedload(Resume.worker))#для связи многие к одному
                 .options(selectinload(Resume.vacancies_replied).load_only(Vacancy.title)) # для связи М2М и один ко многим
                 # load_only подрузит только указанные столбцы
                 )

        result = await session.execute(query)
        result = result.unique().scalars().all()
        print(result)


async def main():
    await create_tables()
    await create_workers()
    # await select_workers()
    # await update_workers()
    await insert_resumes()
    # await select_resumes_avg_compensation()
    # await join_cte_subquery_window_func()
    # await select_workers_with_condition_relationship()
    # await select_workers_with_condition_relationship_contains_eager()
    # await select_workers_with_relationship_contains_eager_with_limit()
    # await get_dtos_mapp()
    # await get_dtos_mapp_with_relationship()
    await add_vacancies_replies()
    await select_resumes_with_all_relationships()


if __name__ == '__main__':
    asyncio.run(main())
