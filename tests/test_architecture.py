from zarreh_agentkit.architecture import contracts_text


def test_bundled_contracts_are_readable() -> None:
    content = contracts_text()
    assert "Layering" in content
    assert "forbidden" in content
