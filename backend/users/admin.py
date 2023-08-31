from django.contrib import admin

from .models import Subscription, User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'password',
        'recipes_of_author',
        'subscriptions_on_author',
    )
    list_display_links = ('id', 'username')
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email')

    def recipes_of_author(self, obj):
        return obj.recipes.all().count()
    recipes_of_author.short_description = 'Количество рецептов у автора'

    def subscriptions_on_author(self, obj):
        return obj.subscriber.all().count()
    subscriptions_on_author.short_description = (
        'Количество подписчиков у автора'
    )


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'user',
    )
    list_display_links = ('id', 'user')
    search_fields = ('user',)


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
