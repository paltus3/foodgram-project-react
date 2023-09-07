from re import match

from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from users.models import Subscription, User


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User.USERNAME_FIELD,
            'password',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.subscriber.filter(author=obj).exists()


class SubscribeSerializer(CustomUserSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if user.subscriber.filter(author=author).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        context = {'request': request}
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeShortSerializer(
            recipes, many=True, context=context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',)


class IngredientInRecipeSerializer(ModelSerializer):
    id = SerializerMethodField(method_name='get_id')
    name = SerializerMethodField(method_name='get_name')
    measurement_unit = SerializerMethodField(
        method_name='get_measurement_unit'
    )

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = AmountIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField(method_name='get_ingredients')
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = AmountIngredient.objects.filter(recipe=obj)
        serializer = IngredientInRecipeSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorite.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shoppingcart.filter(recipe=obj).exists()


class IngredientInRecipeWriteSerializer(ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        model = AmountIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                  many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError(
                'Нужен хотя бы один ингредиент!'
            )
        ingredients_data = [
            ing.get('id') for ing in ingredients
        ]
        if len(ingredients_data) != len(set(ingredients_data)):
            raise ValidationError(
                'Ингредиенты рецепта должны быть уникальными'
            )
        for ing in ingredients:
            if int(ing.get('amount')) < 1:
                raise ValidationError(
                    'Количество ингредиента не может быть меньше 1'
                )
            if int(ing.get('amount')) > 10000:
                raise ValidationError(
                    'Слишком большое количество ингредиента.'
                )
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError(
                'Нужно выбрать хотя бы один тег!'
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError(
                    'Теги должны быть уникальными!'
                )
            tags_list.append(tag)
        return value

    def validate_cooking_time(self, value):
        """Проверяем, что время больше 1 и меньше 1000 минут."""
        if value < 1:
            raise ValidationError(
                'Минимальное время приготовления 1 минута.'
            )
        if value > 1000:
            raise ValidationError(
                'Максимальное время приготовления 1000 минут.'
            )
        return value

    def validate_name(self, name):
        """Проверяем, что название не состоит только из символов и цифр."""
        if match(r'^[\W\d\s]+$', name):
            raise ValidationError(
                'Название не может состоять только из символов и цифр.'
            )
        return name

    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        AmountIngredient.objects.bulk_create(
            [AmountIngredient(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe,
                                        ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_amounts(recipe=instance,
                                        ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance,
                                    context=context).data


class RecipeShortSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
