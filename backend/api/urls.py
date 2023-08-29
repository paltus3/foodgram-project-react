from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = DefaultRouter()
app_name = 'api'

router.register(
    r'(?P<version>v1)/users',
    UserViewSet,
    basename='users'
)

router.register(
    r'(?P<version>v1)/tags',
    TagViewSet,
    basename='tags'
)

router.register(
    r'(?P<version>v1)/ingredients',
    IngredientViewSet,
    basename='ingredients'
)
router.register(
    r'(?P<version>v1)/recipes',
    RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    path('v1/auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
