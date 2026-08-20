from typing import Dict, Any, List

class T24TemplateEngine:
    """
    Parameterized generator for battle-tested T24 / TAFJ / jBASE routines.
    """

    TEMPLATES_META = [
        {
            "id": "validation_routine",
            "name": "Version Validation Hook (.VALIDATE)",
            "category": "Version / UI",
            "description": "Cross-field and business rule validation attached to a VERSION field.",
            "fields": [
                {"name": "routine_name", "label": "Routine Name", "default": "V.VAL.CHECK.LIMIT.EXPIRY"},
                {"name": "table_name", "label": "Primary Table", "default": "LIMIT"},
                {"name": "field_to_validate", "label": "Field to Validate", "default": "LI.EXPIRY.DATE"},
                {"name": "lookup_table", "label": "Lookup Table", "default": "CUSTOMER"}
            ]
        },
        {
            "id": "service_batch",
            "name": "Multi-Threaded Service Batch (.LOAD, .SELECT, Worker)",
            "category": "Batch / Services",
            "description": "Standard Service Framework pattern for high-throughput batch processing.",
            "fields": [
                {"name": "batch_prefix", "label": "Batch Prefix", "default": "BATCH.ACC.SWEEP"},
                {"name": "table_name", "label": "Target Table", "default": "ACCOUNT"},
                {"name": "select_filter", "label": "Select Criteria", "default": "WITH SWEEP.FLAG EQ 'Y'"}
            ]
        },
        {
            "id": "accounting_entries",
            "name": "Balanced Accounting Posting (EB.ACCOUNTING)",
            "category": "Financial Accounting",
            "description": "Programmatic generation of balanced STMT.ENTRY and CATEG.ENTRY records.",
            "fields": [
                {"name": "routine_name", "label": "Routine Name", "default": "POST.CUSTOM.FEE.ENTRIES"},
                {"name": "txn_code", "label": "Transaction Code", "default": "150"},
                {"name": "system_id", "label": "System ID", "default": "AC"}
            ]
        },
        {
            "id": "ofs_processor",
            "name": "OFS Caller & Deep Error Parser",
            "category": "Integration / OFS",
            "description": "Synchronous OFS execution via OFS.GLOBUS.MANAGER with response token parsing.",
            "fields": [
                {"name": "routine_name", "label": "Routine Name", "default": "EXEC.POST.FUNDS.TRANSFER"},
                {"name": "ofs_source", "label": "OFS Source ID", "default": "BATCH.OFS.SRC"},
                {"name": "version_name", "label": "Application / Version", "default": "FUNDS.TRANSFER,ACTR.INPUT"}
            ]
        },
        {
            "id": "nofile_enquiry",
            "name": "NOFILE Enquiry Routine",
            "category": "Reporting / Enquiries",
            "description": "Extracts selection criteria from D.FIELDS/D.RANGE.AND.VALUE and builds dynamic array output.",
            "fields": [
                {"name": "routine_name", "label": "Routine Name", "default": "E.NOF.GET.CUST.TXN.SUMMARY"},
                {"name": "filter_field", "label": "Filter Field", "default": "CUSTOMER.NO"},
                {"name": "source_table", "label": "Source Table", "default": "STMT.ENTRY"}
            ]
        },
        {
            "id": "local_ref_cache",
            "name": "Local Reference Cache (EB.GET.LOCREF)",
            "category": "Utilities",
            "description": "Dynamic extraction and caching of LOCAL.REF field positions.",
            "fields": [
                {"name": "routine_name", "label": "Routine Name", "default": "GET.LOCAL.REF.POSITIONS"},
                {"name": "app_list", "label": "Application List", "default": "CUSTOMER, ACCOUNT"},
                {"name": "field_list", "label": "Field Names", "default": "L.CUST.SEGMENT, L.KYC.STATUS, L.SWEEP.LIMIT"}
            ]
        }
    ]

    def list_templates(self) -> List[Dict[str, Any]]:
        return self.TEMPLATES_META

    def generate(self, template_id: str, params: Dict[str, str]) -> str:
        if template_id == "validation_routine":
            return self._gen_validation(params)
        elif template_id == "service_batch":
            return self._gen_service_batch(params)
        elif template_id == "accounting_entries":
            return self._gen_accounting(params)
        elif template_id == "ofs_processor":
            return self._gen_ofs(params)
        elif template_id == "nofile_enquiry":
            return self._gen_nofile(params)
        elif template_id == "local_ref_cache":
            return self._gen_locref(params)
        else:
            raise ValueError(f"Unknown template ID: {template_id}")

    def _gen_validation(self, p: Dict[str, str]) -> str:
        name = p.get("routine_name", "V.VAL.CHECK.LIMIT.EXPIRY")
        table = p.get("table_name", "LIMIT")
        field = p.get("field_to_validate", "LI.EXPIRY.DATE")
        lookup = p.get("lookup_table", "CUSTOMER")

        return f"""*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE {name}
*-----------------------------------------------------------------------------
* Program Title    : {name}
* Description      : Validates {field} on {table} table before record commit.
* Attachment Point : VERSION -> {table},INPUT as VALIDATION.RTN
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.{table}
    $INSERT I_F.{lookup}

    * Guard Clause: Only execute in Input ('I') or Copy ('C') mode
    IF NOT(V$FUNCTION MATCHES 'I':@VM:'C') THEN
        RETURN
    END

    GOSUB INITIALISE
    GOSUB PROCESS.VALIDATION
    RETURN

*-----------------------------------------------------------------------------
INITIALISE:
*-----------------------------------------------------------------------------
    FN.{lookup} = 'F.{lookup}'
    F.{lookup}  = ''
    CALL OPF(FN.{lookup}, F.{lookup})

    Y.TARGET.VAL = R.NEW({field})
    RETURN

*-----------------------------------------------------------------------------
PROCESS.VALIDATION:
*-----------------------------------------------------------------------------
    IF Y.TARGET.VAL EQ '' THEN
        AF = {field}
        ETEXT = 'EB-MANDATORY.FIELD'
        CALL STORE.END.ERROR
        RETURN
    END

    * Custom validation logic goes here...
    RETURN
*-----------------------------------------------------------------------------
    END"""

    def _gen_service_batch(self, p: Dict[str, str]) -> str:
        prefix = p.get("batch_prefix", "BATCH.ACC.SWEEP")
        table = p.get("table_name", "ACCOUNT")
        criteria = p.get("select_filter", "WITH SWEEP.FLAG EQ 'Y'")

        return f"""*=============================================================================
* COMPONENT 1: COMMON BLOCK (I_{prefix}.COMMON)
*=============================================================================
    COM /{prefix}.COM/ FN.{table}, F.{table}

*=============================================================================
* COMPONENT 2: .LOAD SUBROUTINE ({prefix}.LOAD)
*=============================================================================
* <Rating>0</Rating>
    SUBROUTINE {prefix}.LOAD
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_{prefix}.COMMON

    FN.{table} = 'F.{table}'
    F.{table}  = ''
    CALL OPF(FN.{table}, F.{table})

    RETURN
    END

*=============================================================================
* COMPONENT 3: .SELECT SUBROUTINE ({prefix}.SELECT)
*=============================================================================
* <Rating>0</Rating>
    SUBROUTINE {prefix}.SELECT
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_{prefix}.COMMON

    Y.LIST = ''
    Y.SEL.CMD = 'SELECT ' : FN.{table} : ' {criteria}'
    CALL EB.READLIST(Y.SEL.CMD, Y.LIST, '', Y.COUNT, Y.ERR)

    IF Y.COUNT > 0 THEN
        CALL BATCH.BUILD.LIST('', Y.LIST)
    END

    RETURN
    END

*=============================================================================
* COMPONENT 4: SINGLE RECORD WORKER ({prefix})
*=============================================================================
* <Rating>0</Rating>
    SUBROUTINE {prefix}(Y.REC.ID)
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.{table}
    $INSERT I_{prefix}.COMMON

    IF Y.REC.ID EQ '' THEN
        RETURN
    END

    R.REC = ''
    Y.READ.ERR = ''
    Y.LOCK.RETRY = '20'

    * Lock and Read Record to prevent concurrent race condition
    CALL F.READU(FN.{table}, Y.REC.ID, R.REC, F.{table}, Y.READ.ERR, Y.LOCK.RETRY)
    IF Y.READ.ERR NE '' THEN
        CALL OCOMO('ERROR: Record locked: ' : Y.REC.ID)
        RETURN
    END

    * Process business record logic safely...
    CALL OCOMO('PROCESSED: Record ID ' : Y.REC.ID)

    * Mandatory Lock Release
    CALL F.RELEASE(FN.{table}, Y.REC.ID, F.{table})
    RETURN
    END"""

    def _gen_accounting(self, p: Dict[str, str]) -> str:
        name = p.get("routine_name", "POST.CUSTOM.FEE.ENTRIES")
        txn = p.get("txn_code", "150")
        sys_id = p.get("system_id", "AC")

        return f"""*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE {name}(Y.ACCOUNT.ID, Y.FEE.AMOUNT, Y.PL.CATEGORY, Y.CURRENCY)
*-----------------------------------------------------------------------------
* Description: Creates a balanced Debit STMT.ENTRY and Credit CATEG.ENTRY.
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_F.ACCOUNT
    $INSERT I_F.STMT.ENTRY
    $INSERT I_F.CATEG.ENTRY

    GOSUB INITIALISE
    GOSUB BUILD.STMT.ENTRY
    GOSUB BUILD.CATEG.ENTRY
    GOSUB COMMIT.ACCOUNTING
    RETURN

*-----------------------------------------------------------------------------
INITIALISE:
*-----------------------------------------------------------------------------
    FN.ACCOUNT = 'F.ACCOUNT'
    F.ACCOUNT  = ''
    CALL OPF(FN.ACCOUNT, F.ACCOUNT)

    R.ACC = ''
    Y.ACC.ERR = ''
    CALL F.READ(FN.ACCOUNT, Y.ACCOUNT.ID, R.ACC, F.ACCOUNT, Y.ACC.ERR)
    IF Y.ACC.ERR NE '' THEN
        E = 'EB-INVALID.ACCOUNT'
        RETURN
    END

    Y.CUST.ID   = R.ACC<AC.CUSTOMER>
    Y.COMP.ID   = ID.COMPANY
    ENTRY.ARRAY = ''
    RETURN

*-----------------------------------------------------------------------------
BUILD.STMT.ENTRY:
*-----------------------------------------------------------------------------
    * Debit STMT.ENTRY (Negative Amount)
    R.STMT = ''
    R.STMT<AC.STE.ACCOUNT.NUMBER>    = Y.ACCOUNT.ID
    R.STMT<AC.STE.COMPANY.CODE>      = Y.COMP.ID
    R.STMT<AC.STE.AMOUNT.LCY>        = -1 * Y.FEE.AMOUNT
    R.STMT<AC.STE.TRANSACTION.CODE>  = '{txn}'
    R.STMT<AC.STE.CUSTOMER.ID>       = Y.CUST.ID
    R.STMT<AC.STE.ACCOUNT.OFFICER>   = R.ACC<AC.ACCOUNT.OFFICER>
    R.STMT<AC.STE.PRODUCT.CATEGORY>  = R.ACC<AC.CATEGORY>
    R.STMT<AC.STE.VALUE.DATE>        = TODAY
    R.STMT<AC.STE.CURRENCY>          = Y.CURRENCY
    R.STMT<AC.STE.POSITION.TYPE>     = 'TR'
    R.STMT<AC.STE.OUR.REFERENCE>     = 'TXN-':TODAY:':':Y.ACCOUNT.ID
    R.STMT<AC.STE.SYSTEM.ID>         = '{sys_id}'
    R.STMT<AC.STE.BOOKING.DATE>      = TODAY
    R.STMT<AC.STE.EXPOSURE.DATE>     = TODAY
    R.STMT<AC.STE.CURRENCY.MARKET>   = '1'
    R.STMT<AC.STE.DEPARTMENT.CODE>   = '1'

    ENTRY.ARRAY<1, -1> = LOWER(R.STMT)
    RETURN

*-----------------------------------------------------------------------------
BUILD.CATEG.ENTRY:
*-----------------------------------------------------------------------------
    * Credit CATEG.ENTRY (Positive Amount)
    R.CATEG = ''
    R.CATEG<AC.CAT.COMPANY.CODE>     = Y.COMP.ID
    R.CATEG<AC.CAT.AMOUNT.LCY>       = Y.FEE.AMOUNT
    R.CATEG<AC.CAT.TRANSACTION.CODE> = '{txn}'
    R.CATEG<AC.CAT.PL.CATEGORY>      = Y.PL.CATEGORY
    R.CATEG<AC.CAT.CUSTOMER.ID>      = Y.CUST.ID
    R.CATEG<AC.CAT.ACCOUNT.OFFICER>  = R.ACC<AC.ACCOUNT.OFFICER>
    R.CATEG<AC.CAT.VALUE.DATE>       = TODAY
    R.CATEG<AC.CAT.CURRENCY>         = Y.CURRENCY
    R.CATEG<AC.CAT.POSITION.TYPE>    = 'TR'
    R.CATEG<AC.CAT.OUR.REFERENCE>    = 'TXN-':TODAY:':':Y.ACCOUNT.ID
    R.CATEG<AC.CAT.SYSTEM.ID>        = '{sys_id}'
    R.CATEG<AC.CAT.BOOKING.DATE>     = TODAY
    R.CATEG<AC.CAT.EXPOSURE.DATE>    = TODAY
    R.CATEG<AC.CAT.CURRENCY.MARKET>  = '1'
    R.CATEG<AC.CAT.DEPARTMENT.CODE>  = '1'

    ENTRY.ARRAY<2, -1> = LOWER(R.CATEG)
    RETURN

*-----------------------------------------------------------------------------
COMMIT.ACCOUNTING:
*-----------------------------------------------------------------------------
    CALL EB.ACCOUNTING('{sys_id}', 'SAO', ENTRY.ARRAY, '')
    RETURN
*-----------------------------------------------------------------------------
    END"""

    def _gen_ofs(self, p: Dict[str, str]) -> str:
        name = p.get("routine_name", "EXEC.POST.FUNDS.TRANSFER")
        source = p.get("ofs_source", "BATCH.OFS.SRC")
        version = p.get("version_name", "FUNDS.TRANSFER,ACTR.INPUT")

        return f"""*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE {name}(Y.DEBIT.ACCT, Y.CREDIT.ACCT, Y.AMOUNT, Y.CCY, Y.TXN.ID, Y.STATUS, Y.ERR.MSG)
*-----------------------------------------------------------------------------
* Description: Executes synchronous OFS and parses success/failure tokens.
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE

    Y.TXN.ID   = ''
    Y.STATUS   = ''
    Y.ERR.MSG  = ''
    Y.OFS.SRC  = '{source}'

    * OFS Message Format
    Y.OFS.MSG  = '{version}/I/PROCESS,//' : ID.COMPANY : ','
    Y.OFS.MSG := ',DEBIT.ACCT.NO=' : Y.DEBIT.ACCT
    Y.OFS.MSG := ',CREDIT.ACCT.NO=' : Y.CREDIT.ACCT
    Y.OFS.MSG := ',DEBIT.AMOUNT=' : Y.AMOUNT
    Y.OFS.MSG := ',DEBIT.CURRENCY=' : Y.CCY

    CALL OFS.GLOBUS.MANAGER(Y.OFS.SRC, Y.OFS.MSG)

    * Extract Transaction Key and Response Flag
    Y.TXN.ID = FIELD(Y.OFS.MSG, '/', 1)
    Y.SUCCESS.FLAG = FIELD(FIELD(Y.OFS.MSG, '/', 3), ',', 1)

    IF Y.SUCCESS.FLAG EQ '1' THEN
        Y.STATUS = 'SUCCESS'
    END ELSE
        Y.STATUS = 'FAILED'
        Y.FAIL.SEGMENT = FIELD(Y.OFS.MSG, '//-1/', 2)
        Y.ERR.MSG = FIELD(Y.FAIL.SEGMENT, ',', 2)
    END

    RETURN
    END"""

    def _gen_nofile(self, p: Dict[str, str]) -> str:
        name = p.get("routine_name", "E.NOF.GET.CUST.TXN.SUMMARY")
        filter_fld = p.get("filter_field", "CUSTOMER.NO")
        tbl = p.get("source_table", "STMT.ENTRY")

        return f"""*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE {name}(Y.DATA.OUT)
*-----------------------------------------------------------------------------
* Description: NOFILE Enquiry routine extracting data based on criteria.
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE
    $INSERT I_ENQUIRY.COMMON
    $INSERT I_F.{tbl}

    Y.DATA.OUT = ''
    GOSUB READ.SELECTION.CRITERIA
    IF Y.FILTER.VAL EQ '' THEN
        RETURN
    END

    GOSUB EXTRACT.RECORDS
    RETURN

*-----------------------------------------------------------------------------
READ.SELECTION.CRITERIA:
*-----------------------------------------------------------------------------
    Y.FILTER.VAL = ''
    LOCATE '{filter_fld}' IN D.FIELDS<1> SETTING Y.POS THEN
        Y.FILTER.VAL = D.RANGE.AND.VALUE<Y.POS>
    END
    RETURN

*-----------------------------------------------------------------------------
EXTRACT.RECORDS:
*-----------------------------------------------------------------------------
    FN.{tbl} = 'F.{tbl}'
    F.{tbl}  = ''
    CALL OPF(FN.{tbl}, F.{tbl})

    Y.SEL.CMD = 'SELECT ' : FN.{tbl} : ' WITH {filter_fld} EQ "' : Y.FILTER.VAL : '"'
    Y.ID.LIST = ''
    CALL EB.READLIST(Y.SEL.CMD, Y.ID.LIST, '', Y.COUNT, Y.ERR)

    FOR Y.IDX = 1 TO Y.COUNT
        Y.REC.ID = Y.ID.LIST<Y.IDX>
        R.REC = ''
        CALL F.READ(FN.{tbl}, Y.REC.ID, R.REC, F.{tbl}, Y.READ.ERR)
        IF Y.READ.ERR EQ '' THEN
            * Structure output string delimited by '*'
            Y.LINE = Y.REC.ID : '*' : R.REC<1> : '*' : R.REC<2>
            Y.DATA.OUT<-1> = Y.LINE
        END
    NEXT Y.IDX

    RETURN
*-----------------------------------------------------------------------------
    END"""

    def _gen_locref(self, p: Dict[str, str]) -> str:
        name = p.get("routine_name", "GET.LOCAL.REF.POSITIONS")
        apps = p.get("app_list", "CUSTOMER, ACCOUNT")
        fields = p.get("field_list", "L.CUST.SEGMENT, L.KYC.STATUS, L.SWEEP.LIMIT")

        return f"""*-----------------------------------------------------------------------------
* <Rating>0</Rating>
*-----------------------------------------------------------------------------
    SUBROUTINE {name}
*-----------------------------------------------------------------------------
* Description: Extracts LOCAL.REF positions dynamically via EB.GET.LOCREF.
*-----------------------------------------------------------------------------
    $INSERT I_COMMON
    $INSERT I_EQUATE

    Y.APPL.LIST  = 'CUSTOMER' : @FM : 'ACCOUNT'
    Y.FIELD.LIST = 'L.CUST.SEGMENT' : @VM : 'L.KYC.STATUS' : @FM : 'L.SWEEP.LIMIT'
    Y.POS.LIST   = ''

    CALL EB.GET.LOCREF(Y.APPL.LIST, Y.FIELD.LIST, Y.POS.LIST)

    POS.CUST.SEGMENT = Y.POS.LIST<1, 1>
    POS.KYC.STATUS   = Y.POS.LIST<1, 2>
    POS.SWEEP.LIMIT  = Y.POS.LIST<2, 1>

    RETURN
    END"""
