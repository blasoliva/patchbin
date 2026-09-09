from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import RequestFactory, TestCase

from catalog.admin import ConnectorFamilyAdmin
from catalog.models import ConnectorFamily, ConnectorType


class ConnectorFamilyModelTests(TestCase):
    """Scenario 1 — ConnectorFamily: slug handling, __str__, ordering, uniqueness."""

    def test_slug_is_autofilled_from_name(self):
        fam = ConnectorFamily.objects.create(name="Phone / jack (TS/TRS)")
        self.assertEqual(fam.slug, "phone-jack-tstrs")

    def test_explicit_slug_is_kept(self):
        fam = ConnectorFamily.objects.create(name="XLR", slug="xlr-custom")
        self.assertEqual(fam.slug, "xlr-custom")

    def test_slug_is_not_regenerated_when_name_changes(self):
        fam = ConnectorFamily.objects.create(name="BNC")
        fam.name = "BNC connectors"
        fam.save()
        fam.refresh_from_db()
        self.assertEqual(fam.slug, "bnc")

    def test_str_returns_name(self):
        self.assertEqual(str(ConnectorFamily(name="RCA / phono")), "RCA / phono")

    def test_default_ordering_is_sort_order_then_name(self):
        ConnectorFamily.objects.create(name="Zeta", sort_order=10)
        ConnectorFamily.objects.create(name="Alpha", sort_order=20)
        ConnectorFamily.objects.create(name="Beta", sort_order=10)
        self.assertEqual(
            [f.name for f in ConnectorFamily.objects.all()],
            ["Beta", "Zeta", "Alpha"],
        )

    def test_name_is_unique(self):
        ConnectorFamily.objects.create(name="XLR")
        with self.assertRaises(IntegrityError):
            ConnectorFamily.objects.create(name="XLR")


class ConnectorTypeModelTests(TestCase):
    """Scenario 2 — ConnectorType: slug, __str__, per-family uniqueness, ordering."""

    def setUp(self):
        self.jack = ConnectorFamily.objects.create(name="Phone / jack", sort_order=10)
        self.xlr = ConnectorFamily.objects.create(name="XLR", sort_order=20)

    def test_slug_is_autofilled_from_name(self):
        conn = ConnectorType.objects.create(family=self.xlr, name="XLR3")
        self.assertEqual(conn.slug, "xlr3")

    def test_str_includes_the_family_name(self):
        conn = ConnectorType.objects.create(family=self.xlr, name="XLR3")
        self.assertEqual(str(conn), "XLR3 (XLR)")

    def test_name_is_unique_within_a_family(self):
        ConnectorType.objects.create(family=self.xlr, name="XLR3")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConnectorType.objects.create(family=self.xlr, name="XLR3")

    def test_same_name_is_allowed_under_a_different_family(self):
        ConnectorType.objects.create(family=self.xlr, name="Adapter")
        ConnectorType.objects.create(family=self.jack, name="Adapter")
        self.assertEqual(ConnectorType.objects.filter(name="Adapter").count(), 2)

    def test_names_that_collide_on_slug_are_rejected_within_a_family(self):
        # Different names, same slugify() result -> the slug uniqueness
        # constraint (not the name one) must still reject the second row.
        ConnectorType.objects.create(family=self.xlr, name="TA 3")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConnectorType.objects.create(family=self.xlr, name="TA-3")

    def test_default_ordering_follows_family_then_local_sort(self):
        ConnectorType.objects.create(family=self.xlr, name="B type", sort_order=1)
        ConnectorType.objects.create(family=self.jack, name="A type", sort_order=2)
        ConnectorType.objects.create(family=self.jack, name="Z type", sort_order=1)
        # jack sorts before xlr (family sort_order 10 < 20); within jack,
        # rows order by their own sort_order then name.
        self.assertEqual(
            [t.name for t in ConnectorType.objects.all()],
            ["Z type", "A type", "B type"],
        )


class FamilyDeletionTests(TestCase):
    """Scenario 3 — deleting a family is PROTECTed while it still has types."""

    def setUp(self):
        self.family = ConnectorFamily.objects.create(name="XLR")

    def test_delete_is_blocked_while_types_reference_the_family(self):
        ConnectorType.objects.create(family=self.family, name="XLR3")
        with self.assertRaises(ProtectedError):
            self.family.delete()
        self.assertTrue(ConnectorFamily.objects.filter(pk=self.family.pk).exists())

    def test_delete_succeeds_once_the_types_are_removed(self):
        conn = ConnectorType.objects.create(family=self.family, name="XLR3")
        conn.delete()
        self.family.delete()
        self.assertFalse(ConnectorFamily.objects.filter(pk=self.family.pk).exists())


class CatalogAdminTests(TestCase):
    """Scenario 4 — the admin is the app's only UI today; its pages must render."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("root", "root@example.com", "pw")
        cls.jack = ConnectorFamily.objects.create(name="Phone / jack", sort_order=10)
        cls.xlr = ConnectorFamily.objects.create(name="XLR", sort_order=20)
        ConnectorType.objects.create(family=cls.xlr, name="XLR3")
        ConnectorType.objects.create(family=cls.xlr, name="XLR4")
        ConnectorType.objects.create(family=cls.jack, name="TRS")

    def setUp(self):
        self.client.force_login(self.staff)

    def test_family_changelist_renders(self):
        self.assertEqual(
            self.client.get("/admin/catalog/connectorfamily/").status_code, 200
        )

    def test_type_changelist_renders(self):
        self.assertEqual(
            self.client.get("/admin/catalog/connectortype/").status_code, 200
        )

    def test_family_change_page_with_type_inline_renders(self):
        # Regression: the ConnectorType inline used to declare prepopulated_fields
        # for a field ("slug") absent from its `fields`, which 500'd this page.
        url = f"/admin/catalog/connectorfamily/{self.xlr.pk}/change/"
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_type_add_page_renders(self):
        self.assertEqual(
            self.client.get("/admin/catalog/connectortype/add/").status_code, 200
        )

    def test_family_admin_annotates_type_count(self):
        request = RequestFactory().get("/")
        request.user = self.staff
        model_admin = ConnectorFamilyAdmin(ConnectorFamily, AdminSite())
        counts = {f.name: f._type_count for f in model_admin.get_queryset(request)}
        self.assertEqual(counts, {"Phone / jack": 1, "XLR": 2})


class SampleCatalogFixtureTests(TestCase):
    """Scenario 5 — the shipped sample data loads and is internally consistent."""

    fixtures = ["sample_catalog"]

    def test_expected_row_counts(self):
        self.assertEqual(ConnectorFamily.objects.count(), 12)
        self.assertEqual(ConnectorType.objects.count(), 36)

    def test_every_type_has_a_slug_and_a_family(self):
        for conn in ConnectorType.objects.select_related("family"):
            self.assertTrue(conn.slug, f"{conn.name} has no slug")
            self.assertIsNotNone(conn.family_id)

    def test_family_slugs_are_unique(self):
        slugs = list(ConnectorFamily.objects.values_list("slug", flat=True))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_contact_counts_are_positive_when_set(self):
        for conn in ConnectorType.objects.exclude(contact_count=None):
            self.assertGreater(conn.contact_count, 0)

    def test_every_family_has_at_least_one_type(self):
        empty = ConnectorFamily.objects.filter(types__isnull=True)
        self.assertQuerySetEqual(empty, [])


class DemoUserFixtureTests(TestCase):
    """Scenario 6 — the documented demo credentials actually work."""

    fixtures = ["demo_user"]

    def test_admin_can_authenticate_with_documented_password(self):
        self.assertTrue(
            self.client.login(username="admin", password="patchbin-admin")
        )

    def test_admin_is_a_superuser(self):
        user = User.objects.get(username="admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
