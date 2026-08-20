import pytest
import os
import shutil
from app.linter import T24CodeLinter
from app.templates_engine import T24TemplateEngine
from app.memory_store import T24MemoryStore

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "test_patterns.db")

@pytest.fixture(autouse=True)
def cleanup_test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_linter_clean_code():
    linter = T24CodeLinter()
    clean_code = """* <Rating>0</Rating>
    SUBROUTINE TEST.CLEAN
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.ACCOUNT

    FN.ACCOUNT = 'F.ACCOUNT'
    F.ACCOUNT  = ''
    CALL OPF(FN.ACCOUNT, F.ACCOUNT)

    Y.CNT = 10
    FOR I = 1 TO Y.CNT
        Y.VAL = I
    NEXT I

    RETURN
    END"""
    result = linter.lint(clean_code)
    assert result["score"] >= 80
    assert result["status"] == "PASS"

def test_linter_detect_stop_and_dcount():
    linter = T24CodeLinter()
    bad_code = """SUBROUTINE TEST.BAD
    FOR I = 1 TO DCOUNT(R.REC, @VM)
        STOP
    NEXT I
    END"""
    result = linter.lint(bad_code)
    assert result["status"] == "FAIL"
    issue_ids = [i["id"] for i in result["issues"]]
    assert "T24-R002" in issue_ids  # STOP check
    assert "T24-R003" in issue_ids  # DCOUNT in loop
    assert "T24-R001A" in issue_ids # Missing I_COMMON

def test_template_generation():
    engine = T24TemplateEngine()
    templates = engine.list_templates()
    assert len(templates) >= 5

    code = engine.generate("validation_routine", {
        "routine_name": "V.VAL.CUSTOM",
        "table_name": "ACCOUNT",
        "field_to_validate": "AC.WORKING.BALANCE",
        "lookup_table": "CUSTOMER"
    })
    assert "SUBROUTINE V.VAL.CUSTOM" in code
    assert "$INSERT I_F.ACCOUNT" in code
    assert "CALL OPF(FN.CUSTOMER, F.CUSTOMER)" in code

def test_memory_store_learning_and_context_injection():
    store = T24MemoryStore(db_path=TEST_DB_PATH)
    
    sample_code = """* <Rating>0</Rating>
    SUBROUTINE V.VAL.BANK.CUSTOM.KYC
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.BANK.CUSTOM.KYC
    $INSERT I_F.CUSTOMER

    FN.BANK.CUSTOM.KYC = 'F.BANK.CUSTOM.KYC'
    F.BANK.CUSTOM.KYC = ''
    CALL OPF(FN.BANK.CUSTOM.KYC, F.BANK.CUSTOM.KYC)

    * Custom rule: Check KYC Level 4
    RETURN
    END"""

    # Ingest sample
    result = store.add_sample(
        title="Custom KYC Validation Pattern",
        category="Validation Hook",
        code=sample_code,
        tags="KYC, CUSTOMER",
        notes="Bank standard for custom table F.BANK.CUSTOM.KYC"
    )

    assert result["extracted_routine_name"] == "V.VAL.BANK.CUSTOM.KYC"
    assert "I_F.BANK.CUSTOM.KYC" in result["extracted_inserts"]
    assert "BANK.CUSTOM.KYC" in result["extracted_tables"]

    # Verify listing
    samples = store.list_samples()
    assert len(samples) == 1
    assert samples[0]["title"] == "Custom KYC Validation Pattern"

    # Verify prompt context generation
    context = store.get_learning_context_for_prompt("Generate KYC routine")
    assert "V.VAL.BANK.CUSTOM.KYC" in context
    assert "I_F.BANK.CUSTOM.KYC" in context

    # Test deletion
    deleted = store.delete_sample(samples[0]["id"])
    assert deleted is True
    assert len(store.list_samples()) == 0
