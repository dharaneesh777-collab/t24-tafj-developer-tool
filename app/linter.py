import re
from typing import List, Dict, Any

class T24CodeLinter:
    """
    Static analyzer for Temenos T24 / TAFJ / jBASE Infobasic source code.
    Enforces official Temenos coding standards, concurrency protocols, and performance guidelines.
    """

    def __init__(self):
        pass

    def lint(self, code: str) -> Dict[str, Any]:
        lines = code.split("\n")
        issues: List[Dict[str, Any]] = []

        has_i_common = False
        has_i_equate = False
        has_rating_tag = False
        has_f_readu = False
        has_f_release = False
        
        opened_tables = set()
        read_tables = set()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Skip full comment lines (* or !)
            if stripped.startswith("*") or stripped.startswith("!"):
                if "<Rating>" in line:
                    has_rating_tag = True
                continue

            # Check 1: Inserts
            if re.search(r"\$INSERT\s+I_COMMON", stripped, re.IGNORECASE):
                has_i_common = True
            if re.search(r"\$INSERT\s+I_EQUATE", stripped, re.IGNORECASE):
                has_i_equate = True

            # Check 2: STOP or ABORT in routines
            if re.search(r"\b(STOP|ABORT)\b", stripped, re.IGNORECASE) and not stripped.startswith("*"):
                issues.append({
                    "id": "T24-R002",
                    "severity": "CRITICAL",
                    "line": idx,
                    "code_snippet": stripped,
                    "title": "Prohibited STOP / ABORT in Routine",
                    "message": "Using STOP or ABORT terminates the underlying TAFJ servlet worker thread or jBASE process. Replace with 'CALL STORE.END.ERROR' and 'RETURN' or graceful error handling.",
                    "suggestion": "CALL STORE.END.ERROR\nRETURN"
                })

            # Check 3: Uncounted DCOUNT in FOR loop
            dcount_for_match = re.search(r"FOR\s+\w+\s*=\s*\d+\s+TO\s+DCOUNT\s*\(", stripped, re.IGNORECASE)
            if dcount_for_match:
                issues.append({
                    "id": "T24-R003",
                    "severity": "WARNING",
                    "line": idx,
                    "code_snippet": stripped,
                    "title": "Performance: Uncalculated DCOUNT in Loop Header",
                    "message": "DCOUNT() called inside a FOR loop evaluation is recomputed on every iteration, leading to O(N^2) complexity. Pre-calculate the count into a variable prior to the loop.",
                    "suggestion": "Y.CNT = DCOUNT(R.ARRAY, @VM)\nFOR I.VAR = 1 TO Y.CNT"
                })

            # Check 4: Record Locking tracking
            if re.search(r"CALL\s+F\.READU\s*\(", stripped, re.IGNORECASE):
                has_f_readu = True
                # Extract table name if possible
                tbl_match = re.search(r"CALL\s+F\.READU\s*\(\s*([A-Za-z0-9_.]+)", stripped, re.IGNORECASE)
                if tbl_match:
                    read_tables.add(tbl_match.group(1).strip())

            if re.search(r"CALL\s+F\.RELEASE\s*\(", stripped, re.IGNORECASE):
                has_f_release = True

            # Check 5: OPF Tracking
            opf_match = re.search(r"CALL\s+OPF\s*\(\s*([A-Za-z0-9_.]+)\s*,\s*([A-Za-z0-9_.]+)\s*\)", stripped, re.IGNORECASE)
            if opf_match:
                opened_tables.add(opf_match.group(1).strip())

            # Check 6: Direct READ / WRITE instead of standard F.READ / F.WRITE
            if re.search(r"^\s*(READ|READU|WRITE|MATREAD|MATWRITE)\s+[A-Za-z0-9_.]+\s+FROM\s+", stripped, re.IGNORECASE):
                issues.append({
                    "id": "T24-R006",
                    "severity": "ERROR",
                    "line": idx,
                    "code_snippet": stripped,
                    "title": "Direct jBASE File I/O Anti-Pattern",
                    "message": "Direct READ/WRITE bypasses T24 multi-company routing, concurrency controls, and TAFJ cache invalidation. Use CALL F.READ, CALL F.READU, or CALL F.WRITE instead.",
                    "suggestion": "CALL F.READ(FN.TABLE, Y.ID, R.REC, F.TABLE, Y.ERR)"
                })

            # Check 7: Hardcoded Company Mnemonics
            if re.search(r"['\"](FBNK\.|FNOM\.|F\.\w+\$NAU)['\"]", stripped, re.IGNORECASE):
                issues.append({
                    "id": "T24-R007",
                    "severity": "WARNING",
                    "line": idx,
                    "code_snippet": stripped,
                    "title": "Hardcoded Company Table Prefix",
                    "message": "Hardcoding table prefixes like 'FBNK.' breaks multi-company and multi-book environments. Always pass the base table name to CALL OPF(FN.TABLE, F.TABLE).",
                    "suggestion": "FN.ACCOUNT = 'F.ACCOUNT'\nF.ACCOUNT = ''\nCALL OPF(FN.ACCOUNT, F.ACCOUNT)"
                })

            # Check 8: Error assignment without STORE.END.ERROR or ERR
            if re.search(r"^\s*ETEXT\s*=\s*", stripped, re.IGNORECASE):
                # Look ahead next 4 lines to ensure STORE.END.ERROR is called
                following_code = "\n".join(lines[idx:min(idx + 4, len(lines))])
                if "STORE.END.ERROR" not in following_code and "ERR" not in following_code:
                    issues.append({
                        "id": "T24-R009",
                        "severity": "INFO",
                        "line": idx,
                        "code_snippet": stripped,
                        "title": "Uncommitted Error Variable Assignment",
                        "message": "Setting ETEXT alone will not stop the screen transaction without invoking CALL STORE.END.ERROR.",
                        "suggestion": "ETEXT = 'EB-ERROR.CODE'\nCALL STORE.END.ERROR"
                    })

        # Global Checks across file
        if not has_i_common:
            issues.append({
                "id": "T24-R001A",
                "severity": "ERROR",
                "line": 1,
                "code_snippet": "$INSERT I_COMMON missing",
                "title": "Missing $INSERT I_COMMON",
                "message": "T24 subroutines must include '$INSERT I_COMMON' to access global banking variables (ID.NEW, R.NEW, TODAY, etc.).",
                "suggestion": "$INSERT I_COMMON"
            })

        if not has_i_equate:
            issues.append({
                "id": "T24-R001B",
                "severity": "ERROR",
                "line": 1,
                "code_snippet": "$INSERT I_EQUATE missing",
                "title": "Missing $INSERT I_EQUATE",
                "message": "T24 subroutines must include '$INSERT I_EQUATE' for standard framework constants (@FM, @VM, @SM, @TM, etc.).",
                "suggestion": "$INSERT I_EQUATE"
            })

        if not has_rating_tag:
            issues.append({
                "id": "T24-R008",
                "severity": "INFO",
                "line": 1,
                "code_snippet": "Missing <Rating> tag",
                "title": "Missing Code Rating Header Tag",
                "message": "Temenos standards recommend starting subroutines with a <Rating>0</Rating> tag for static quality metrics.",
                "suggestion": "* <Rating>0</Rating>"
            })

        if has_f_readu and not has_f_release:
            issues.append({
                "id": "T24-R004",
                "severity": "CRITICAL",
                "line": 1,
                "code_snippet": "F.READU detected without matching F.RELEASE",
                "title": "Potential Record Deadlock: Missing F.RELEASE",
                "message": "A record is locked with F.READU, but no F.RELEASE call was found. This can cause persistent lock contention and freeze online/batch processes.",
                "suggestion": "CALL F.RELEASE(FN.TABLE, Y.ID, F.TABLE)"
            })

        score = max(0, 100 - sum(
            30 if i["severity"] == "CRITICAL" else
            20 if i["severity"] == "ERROR" else
            10 if i["severity"] == "WARNING" else 5
            for i in issues
        ))

        return {
            "total_issues": len(issues),
            "score": score,
            "status": "PASS" if score >= 80 and not any(i["severity"] in ["CRITICAL", "ERROR"] for i in issues) else "FAIL",
            "issues": issues
        }
