from django.contrib import admin
from recipes.models import (AmountIngredient, Carts, Favorite, Ingredient,
                            Recipe, RecipeTags, Tag)


class TagAdmin(admin.ModelAdmin):
    fields = ('name', 'slug', 'color',)
    list_display = ('name', 'color', 'slug')
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    fields = ('name', 'measurement_unit',)
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name__startswith',)


class AmountIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
    list_filter = ('recipe',)


class RecipeIngredientsInLine(admin.TabularInline):
    model = AmountIngredient
    extra = 1
    min_num = 1


class RecipeTagsInLine(admin.TabularInline):
    model = RecipeTags
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
    )
    inlines = (RecipeIngredientsInLine, RecipeTagsInLine)
    list_display = ('name', 'author', 'add_in_favorites')
    readonly_fields = ('add_in_favorites',)
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('tags',)
    list_filter = ('author', 'name',)

    def add_in_favorites(self, obj):
        return obj.favorite.all().count()

    add_in_favorites.short_description = 'Количество в избранном'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(AmountIngredient, AmountIngredientAdmin)
admin.site.register(Favorite)
admin.site.register(Carts)
