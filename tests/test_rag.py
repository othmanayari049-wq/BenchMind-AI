from benchmind.models import Evidence, EvidenceKind
from benchmind.rag import EngineeringRetriever


def test_retriever_preserves_pdf_page_reference() -> None:
    evidence = Evidence(
        filename="sensor.pdf",
        kind=EvidenceKind.PDF,
        text="[PAGE 1]\nOverview\n[PAGE 2]\nAbsolute maximum voltage is 3.6 V for the input pin.",
    )
    results = EngineeringRetriever([evidence], chunk_chars=120).search("maximum input voltage", limit=1)
    assert results
    assert results[0].page == 2
    assert results[0].label == "sensor.pdf"
