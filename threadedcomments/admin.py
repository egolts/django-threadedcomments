from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ungettext
from django.contrib.comments.admin import CommentsAdmin

from threadedcomments.models import ThreadedComment
from django.contrib import comments
from django.contrib.comments import signals

def hide_comments(modeladmin, request, queryset):
    queryset.update(is_public = False)
hide_comments.short_description = "Hide selected comments"


def show_comments(modeladmin, request, queryset):
    queryset.update(is_public = True)
show_comments.short_description = "Show selected comments"


class ThreadedCommentsAdmin(CommentsAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'object_pk', 'site')}
        ),

        (_('Content'),
           {'fields': ('user', 'comment')}
        ),
        (_('Hierarchy'),
           {'fields': ('parent',)}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        ),
    )

    list_display = ('name', 'content_type', 'object_pk', 'parent',
                    'ip_address', 'submit_date', 'is_public', 'is_removed')
    search_fields = ('comment', 'user__username','ip_address')
    raw_id_fields = ("parent",)
    
    actions = [hide_comments, show_comments]
    
    def get_actions(self, request):
        actions = super(ThreadedCommentsAdmin, self).get_actions(request)
        if 'approve_comments' in actions:
            del actions['approve_comments']
        del actions['flag_comments']
        return actions

    
admin.site.register(ThreadedComment, ThreadedCommentsAdmin)

