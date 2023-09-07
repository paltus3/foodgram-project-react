from colorfield.fields import ColorField
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Название'
    )
    color = ColorField(
        max_length=7,
        unique=True,
        verbose_name='Цветовой HEX-код'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='slug',
        validators=[RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$',
            message='Слаг тега содержит недопустимый символ'
        )]
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=30,
        verbose_name='Единицы измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement_unit'
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='AmountIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления не может быть меньше 1 минуты'
            ),
            MaxValueValidator(
                10000,
                message='Время приготовления не может быть больше 1000 минут'
            )
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    def add_ingredient_amount(self, ingredient, amount):
        self.ingredients.add(ingredient, through_defaults={'amount': amount})

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class AmountIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(
                1,
                message='Количество ингредиента не может быть меньше 1'
            ),
            MaxValueValidator(
                10000,
                message='Количество ингредиента не может быть больше 10000'
            )
        ],
    )

    class Meta:
        ordering = ('ingredient',)
        verbose_name = 'Ингредиент и количество'
        verbose_name_plural = 'Ингредиенты и количество'

    def __str__(self):
        return f'{self.ingredient} в рецепте {self.recipe}'


class RecipeTags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг'
    )

    class Meta:
        verbose_name = 'Тэги'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'У рецепта {self.recipe} есть тэг {self.tag}'


class FavCartBase(models.Model):
    class Meta:
        abstract = True
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            ),
        )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь'
    )

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'


class Favorite(FavCartBase):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(FavCartBase):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
