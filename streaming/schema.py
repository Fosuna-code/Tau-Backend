import strawberry
from .models import Movie, Category
from strawberry.file_uploads import Upload

# 1. Define the "Type" (The Shape of Data)
# This tells GraphQL exactly what fields are available to the frontend.
@strawberry.django.type(Category)
class CategoryType:
    id: strawberry.ID
    name: str
    slug: str

@strawberry.django.type(Movie)
class MovieType:
    id: strawberry.ID
    title: str
    description: str
    year: int
    duration_minutes: int
    duration_formatted: str
    is_new:bool
    is_student_production:bool
    is_from_festival: bool
    categories: list[CategoryType]

    @strawberry.field
    def poster_mobile_url(self) -> str:
        if self.poster_mobile:
            return self.poster_mobile.url
        return ""

    @strawberry.field
    def poster_desktop_url(self) -> str:
        if self.poster_desktop:
            return self.poster_desktop.url
        return ""

    @strawberry.field
    def poster_original_url(self) -> str:
        if self.poster_original:
            return self.poster_original.url
        return ""

    @strawberry.field
    def backdrop_original_url(self) -> str:
        if self.backdrop_original:
            return self.backdrop_original.url
        return ""
    # Note: We can exclude 'is_active' if we don't want the frontend to see it

# 2. Define the "Query" (The Logic)
# This is your "View". It tells Django how to fetch the data.
@strawberry.type
class Query:
    @strawberry.field
    def movies(self) -> list[MovieType]:
        return Movie.objects.filter(is_active=True)

    @strawberry.field
    def categories(self) -> list[CategoryType]:
        return Category.objects.all()

    @strawberry.field
    def movies_by_category(self, category_slug: str) -> list[MovieType]:
        return Movie.objects.filter(is_active=True, categories__slug=category_slug)

@strawberry.input
class CategoryInput: 
    name: str
    slug:str
@strawberry.input
class MovieInput:
    title: str
    description: str
    year: int
    duration_minutes: int
    category_ids: list[strawberry.ID]
    is_new:bool
    is_student_production:bool
    is_from_festival: bool 
    poster_original: Upload | None = None
    backdrop_original: Upload | None = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_category(self, category_data: CategoryInput) -> CategoryType:
        category = Category.objects.create(
            name=category_data.name,
            slug=category_data.slug
        )
        return category

    @strawberry.mutation
    def create_movie(self, movie_data: MovieInput) -> MovieType:
        # Create the movie instance without the files first
        movie = Movie.objects.create(
            title=movie_data.title,
            description=movie_data.description,
            year=movie_data.year,
            duration_minutes=movie_data.duration_minutes,
            poster_original=movie_data.poster_original,
            backdrop_original=movie_data.backdrop_original,
            is_new = movie_data.is_new,
            is_student_production = movie_data.is_student_production,
            is_from_festival = movie_data.is_from_festival
        )
        movie.categories.set(movie_data.category_ids)
        return movie

    @strawberry.mutation
    def update_movie(self, movie_id: strawberry.ID, movie_data: MovieInput) -> MovieType:
        movie = Movie.objects.get(id=movie_id)
        movie.title = movie_data.title
        movie.description = movie_data.description
        movie.year = movie_data.year
        movie.duration_minutes = movie_data.duration_minutes
        
        if movie_data.poster_original:
            movie.poster_original = movie_data.poster_original
        if movie_data.backdrop_original:
            movie.backdrop_original = movie_data.backdrop_original
            
        movie.save()
        movie.categories.set(movie_data.category_ids)
        return movie

    @strawberry.mutation
    def delete_movie(self, movie_id: strawberry.ID) -> bool:
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.delete()
            return True
        except Movie.DoesNotExist:
            return False
 
    @strawberry.mutation
    def delete_all_movies(self) -> int:
        count, _ = Movie.objects.all().delete()
        return count

# 3. Create the Schema object
# schema = strawberry.Schema(query=Query, mutation=Mutation)
