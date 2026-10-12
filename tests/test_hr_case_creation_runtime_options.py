from types import SimpleNamespace

from application.bootstrap.hr_case_creation_factory import HrCaseCreationRuntime


class FakeProfiles:
    def __init__(self):
        self.structure_refs = []

    def list_profiles(self, *, structure_ref):
        self.structure_refs.append(structure_ref)
        return (
            SimpleNamespace(
                organization=SimpleNamespace(code="urssaf", label="URSSAF Bretagne")
            ),
            SimpleNamespace(
                organization=SimpleNamespace(code="mutuelle", label="Mutuelle PMSL")
            ),
        )


class FakeReader:
    def __init__(self):
        self.closed = False

    def lire_identites(self):
        return (
            SimpleNamespace(IDpersonne=42, nom="DUPONT", prenom="Alice"),
            SimpleNamespace(IDpersonne=7, nom="", prenom=""),
        )

    def close(self):
        self.closed = True


def test_creation_runtime_lists_only_configured_organizations():
    profiles = FakeProfiles()
    reader = FakeReader()
    runtime = HrCaseCreationRuntime(
        _structure_ref="structure-a",
        _service=object(),
        _profile_repository=profiles,
        _person_reader_factory=lambda: reader,
    )

    options = runtime.list_organizations()

    assert [(item.code, item.label) for item in options] == [
        ("mutuelle", "Mutuelle PMSL"),
        ("urssaf", "URSSAF Bretagne"),
    ]
    assert profiles.structure_refs == ["structure-a"]


def test_creation_runtime_maps_person_reader_and_closes_it():
    profiles = FakeProfiles()
    reader = FakeReader()
    runtime = HrCaseCreationRuntime(
        _structure_ref="structure-a",
        _service=object(),
        _profile_repository=profiles,
        _person_reader_factory=lambda: reader,
    )

    options = runtime.list_people()

    assert [(item.identifier, item.label) for item in options] == [
        ("42", "DUPONT Alice"),
        ("7", "Personne #7"),
    ]
    assert reader.closed is True


def test_creation_runtime_options_do_not_expose_structure_identity():
    profiles = FakeProfiles()
    runtime = HrCaseCreationRuntime(
        _structure_ref="structure-secret",
        _service=object(),
        _profile_repository=profiles,
        _person_reader_factory=FakeReader,
    )

    assert all(
        "structure-secret" not in repr(item)
        for item in runtime.list_organizations() + runtime.list_people()
    )
