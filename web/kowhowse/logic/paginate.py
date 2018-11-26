from ..bitter import *


class Paginator:
    feed_classes = [SectionFeed, AbFeed, AbxFeed, MushraFeed, MosFeed, NullFeed]

    def __init__(self, survey, subject):
        self._survey = survey
        self._subject = subject
        self._current = None

    def __enter__(self):
        def create_page(sender, instance, *args, **kwargs):
            if instance.page is None:
                page = Page(survey=self._survey, subject=self._subject)
                page.save()
                if self._current is not None:
                    self._current.next_page = page
                    self._current.save()
                    page.prev_page = self._current
                    page.save()
                else:
                    page.is_current = True
                    page.save()
                self._current = page
                instance.page = page

        for c in Paginator.feed_classes:
            signals.pre_save.connect(
                create_page,
                sender=c,
                weak=False,
                dispatch_uid='create_page_{}'.format(c.__name__)
            )
        NullFeed().save()

    def __exit__(self, exc_type, exc_value, exc_tb):
        NullFeed().save()
        for c in Paginator.feed_classes:
            signals.pre_save.disconnect(
                sender=c,
                dispatch_uid='create_page_{}'.format(c.__name__)
            )
