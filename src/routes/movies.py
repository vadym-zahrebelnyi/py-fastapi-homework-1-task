import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import await_only

from database import get_db, MovieModel
from schemas import  MovieListResponseSchema, MovieDetailResponseSchema


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
) -> MovieListResponseSchema:
    total_count = await db.scalar(select(func.count(MovieModel.id)))


    total_pages = math.ceil(total_count / per_page)
    offset = (page - 1) * per_page
    if total_count == 0 or offset >= total_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    fetched_movies = (
        await db.scalars(
            select(MovieModel)
            .offset(offset)
            .limit(per_page)
        )
    ).all()


    prefix_url = "/theater/movies/"

    prev_page = None
    if page > 1:
        prev_page = f"{prefix_url}?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"{prefix_url}?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=list(fetched_movies),
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_count
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailResponseSchema:
    if not (movie_detail := await db.get(MovieModel, movie_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailResponseSchema.model_validate(
        movie_detail, from_attributes=True
    )

