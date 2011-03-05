from django.core.management.base import NoArgsCommand
from django.contrib.sites.models import Site
from django.db import transaction, connection
from django.conf import settings

from threadedcomments.models import ThreadedComment

USER_SQL = """
SELECT
    id,
    content_type_id,
    object_id,
    parent_id,
    user_id,
    date_submitted,
    date_modified,
    date_approved,
    comment,
    markup,
    is_public,
    is_approved,
    ip_address
FROM threadedcomments_threadedcomment
"""

#WHERE parent_id is not NULL ORDER BY id ASC

FREE_SQL = """
SELECT
    content_type_id,
    object_id,
    parent_id,
    name,
    website,
    email,
    date_submitted,
    date_modified,
    date_approved,
    comment,
    markup,
    is_public,
    is_approved,
    ip_address
FROM threadedcomments_freethreadedcomment
"""

PATH_SEPARATOR = getattr(settings, 'COMMENT_PATH_SEPARATOR', '/')
PATH_DIGITS = getattr(settings, 'COMMENT_PATH_DIGITS', 10)

class Command(NoArgsCommand):
    help = "Migrates django-threadedcomments <= 0.5 to the new model structure"

    def handle(self, *args, **options):
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)

        site = Site.objects.all()[0]

        cursor = connection.cursor()
        cursor.execute(FREE_SQL)
        for row in cursor:
            (content_type_id, object_id, parent_id, name, website, email,
                date_submitted, date_modified, date_approved, comment, markup,
                is_public, is_approved, ip_address) = row
            tc = ThreadedComment(
                content_type_id=content_type_id,
                object_pk=object_id,
                user_name=name,
                user_email=email,
                user_url=website,
                comment=comment,
                submit_date=date_submitted,
                ip_address=ip_address,
                is_public=is_public,
                is_removed=not is_approved,
                parent_id=parent_id,
                site=site,
            )
            tc.save(skip_tree_path=True)

        cursor = connection.cursor()
        cursor.execute(USER_SQL)
        for row in cursor:
            (id, content_type_id, object_id, parent_id, user_id, date_submitted,
                date_modified, date_approved, comment, markup, is_public,
                is_approved, ip_address) = row
            tc = ThreadedComment(
                comment_ptr_id=id,
                content_type_id=content_type_id,
                object_pk=object_id,
                user_id=user_id,
                comment=comment,
                submit_date=date_submitted,
                ip_address=ip_address,
                is_public=is_public,
                is_removed=False,
                parent_id=parent_id,
                site=site,
            )
            tc.save(skip_tree_path=True)
            print '----'
            print id
            print 'saved'

        for comment in ThreadedComment.objects.all():
            path = [str(comment.id).zfill(PATH_DIGITS)]
            current = comment
            while current.parent:
                current = current.parent
                path.append(str(current.id).zfill(PATH_DIGITS))
            comment.tree_path = PATH_SEPARATOR.join(reversed(path))
            
            print '-----'
            print 'before second save'
            print comment.pk
            
            comment.save(skip_tree_path=True)
            
            if comment.parent:
                print '---'
                print comment.pk
                print 'updated - before last step'
                
                ThreadedComment.objects.filter(pk=comment.parent.pk).update(
                    last_child=comment)
                

        transaction.commit()
        transaction.leave_transaction_management()
