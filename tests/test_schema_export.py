from boutiques.schema_export import VERSIONS, export_all, schema_for


def test_schema_for_each_version_has_required_fields():
    for version in VERSIONS:
        schema = schema_for(version)
        assert schema.get("title")
        assert "properties" in schema
        for required in ("name", "description", "command-line", "schema-version", "inputs", "tool-version"):
            assert required in schema["properties"], f"{version} missing {required}"


def test_export_all_writes_files(tmp_path):
    written = export_all(tmp_path)
    assert {p.parent.name for p in written} == set(VERSIONS)
    for path in written:
        assert path.name == "descriptor.schema.json"
        assert path.stat().st_size > 100
