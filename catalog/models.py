from django.db import models
from django.utils.text import slugify


class ConnectorFamily(models.Model):
    """A physical/electrical connector standard (XLR, phone jack, RCA, ...).

    Families are the top-level taxonomy used to filter the catalogue. An
    individual connector belongs to a family as a ``ConnectorType``.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower numbers sort first in lists.",
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "connector family"
        verbose_name_plural = "connector families"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ConnectorType(models.Model):
    """A specific connector within a family, e.g. XLR3, quarter-inch TRS, DB25.

    Gender, right-angle vs straight, and locking are properties of an individual
    cable end rather than of the connector itself, so they are not stored here.
    """

    family = models.ForeignKey(
        ConnectorFamily,
        on_delete=models.PROTECT,
        related_name="types",
    )
    name = models.CharField(
        max_length=100,
        help_text='Specific connector within the family, e.g. "XLR3" or "TRS".',
    )
    slug = models.SlugField(max_length=100, blank=True)
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        help_text='Common shorthand, e.g. "TT" or "TRS".',
    )
    contact_count = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Number of pins / poles / conductors (3 for XLR3, 2 for TS).",
    )
    description = models.TextField(blank=True)
    typical_uses = models.TextField(
        blank=True,
        help_text="Common signals or gear this connector is used for.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to retire a connector without deleting historical data.",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower numbers sort first within the family.",
    )

    class Meta:
        ordering = ["family__sort_order", "family__name", "sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "name"],
                name="unique_connectortype_name_per_family",
            ),
            models.UniqueConstraint(
                fields=["family", "slug"],
                name="unique_connectortype_slug_per_family",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.family.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
