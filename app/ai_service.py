import os
import httpx
from typing import Dict, Any, List, Optional
from app.memory_store import T24MemoryStore

BASE_SYSTEM_PROMPT = """You are the Lead Temenos T24 Technical Analyst and Master Core Banking Architect with 15+ years of verified production expertise in T24 Core Banking, TAFJ (Temenos Application Framework Java), TAFC / jBASE, Infobasic, and Transact architecture (R08 through R24+).

Follow these non-negotiable rules:
1. Zero Hallucination: Never invent routines, variables, insert files, or API signatures.
2. Complete Code: Always output complete, ready-to-compile subroutines with standard headers (<Rating>0</Rating>), I_COMMON/I_EQUATE inserts, parameter declarations, OPF table resolution, and full error trapping.
3. Concurrency & Safety: Always use F.READU with retry logic when mutating records, and release locks unconditionally with F.RELEASE on all exit branches. Never use STOP or ABORT in online routines.
4. TAFJ & Database Integrity: Respect JVM memory constraints, release dynamic arrays, pre-calculate DCOUNT() bounds, and never recommend direct SQL mutations on underlying RDBMS tables.
5. Ingest & Apply Learned Conventions: Adapt strictly to the user's custom tables, inserts, and naming patterns provided in the learned memory context.
"""

class T24AIService:
    """
    AI Service supporting live LLMs (Gemini / OpenAI) and dynamic in-context memory from learned user code.
    """

    def __init__(self, memory_store: Optional[T24MemoryStore] = None):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.memory_store = memory_store or T24MemoryStore()

    async def generate_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        # Retrieve learned samples from memory
        learned_context = self.memory_store.get_learning_context_for_prompt(user_query)
        effective_system_prompt = BASE_SYSTEM_PROMPT
        if learned_context:
            effective_system_prompt += "\n\n" + learned_context

        # Check if Gemini API key is available
        if self.gemini_api_key:
            try:
                return await self._call_gemini(user_query, effective_system_prompt, chat_history)
            except Exception as e:
                print(f"[WARN] Gemini call failed: {e}. Falling back to Expert Engine.")

        # Check if OpenAI API key is available
        if self.openai_api_key:
            try:
                return await self._call_openai(user_query, effective_system_prompt, chat_history)
            except Exception as e:
                print(f"[WARN] OpenAI call failed: {e}. Falling back to Expert Engine.")

        # Default: Fallback Expert Response Engine with learned memory integration
        return self._expert_fallback_engine(user_query, learned_context)

    async def _call_gemini(self, user_query: str, system_prompt: str, chat_history: List[Dict[str, str]]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.gemini_api_key}"
        
        contents = [
            {"role": "user", "parts": [{"text": system_prompt + "\n\nUser Query: " + user_query}]}
        ]

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json={"contents": contents})
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(self, user_query: str, system_prompt: str, chat_history: List[Dict[str, str]]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _expert_fallback_engine(self, query: str, learned_context: str = "") -> str:
        q = query.lower()
        response_prefix = ""
        if learned_context:
            response_prefix = "> 💡 **Context Note**: Integrated learned conventions from your custom sample library.\n\n"

        if "lock" in q or "f.readu" in q or "f.release" in q or "deadlock" in q:
            return response_prefix + """### T24 Concurrency & Record Locking Architecture

In Temenos T24 and TAFJ, record concurrency is governed by the **Lock Manager** and the `F.RECORD.LOCK` table:

1. **Shared Read (`F.READ`)**:
   - Reads data without taking a lock. Suitable for enquiries, conversions, and read-only validation.
2. **Exclusive Read with Lock (`F.READU`)**:
   - Takes a persistent lock on the record key.
   - Always supply an explicit retry parameter (e.g. `'20'`).
3. **Mandatory Lock Release (`F.RELEASE`)**:
   - If an error occurs or the transaction is aborted, you **MUST** call `CALL F.RELEASE(FN.TABLE, Y.ID, F.TABLE)`.
   - Failing to release a lock will leave an orphaned entry in `F.RECORD.LOCK`, freezing batch threads and online users.

```basic
* Standard Concurrency Pattern
    CALL F.READU(FN.ACCOUNT, Y.ACC.ID, R.ACC, F.ACCOUNT, Y.ERR, '20')
    IF Y.ERR NE '' THEN
        CALL OCOMO('LOCKED: Cannot access account ' : Y.ACC.ID)
        RETURN
    END

    * Perform mutations safely...

    * Release Lock
    CALL F.RELEASE(FN.ACCOUNT, Y.ACC.ID, F.ACCOUNT)
```"""

        elif "accounting" in q or "stmt.entry" in q or "categ.entry" in q or "eb.accounting" in q:
            return response_prefix + """### EB.ACCOUNTING Core Integration

To generate accounting entries programmatically in T24:
1. **Net Zero Balancing**: Total `AMOUNT.LCY` across `STMT.ENTRY` (Customer) and `CATEG.ENTRY` (Internal/PL) dynamic arrays must net to exactly `0.00`.
2. **Sign Convention**:
   - Negative (`-100.00`) = Debit.
   - Positive (`+100.00`) = Credit.
3. **Call Signature**:
   ```basic
   * ENTRY.ARRAY<1> = STMT.ENTRY dynamic array
   * ENTRY.ARRAY<2> = CATEG.ENTRY dynamic array
   CALL EB.ACCOUNTING('AC', 'SAO', ENTRY.ARRAY, '')
   ```"""

        else:
            return response_prefix + f"""### Temenos T24 / TAFJ Architect Expert Response

Regarding your query: *"{query}"*

**Key Architectural Guidelines**:
1. **File Access**: Always resolve multi-company prefixes with `CALL OPF(FN.TABLE, F.TABLE)`.
2. **Error Handling**: Set `AF`, `AV`, `AS`, assign `ETEXT = 'EB-YOUR.MESSAGE'`, and invoke `CALL STORE.END.ERROR`. Never use `STOP` or `ABORT` in online routines.
3. **TAFJ Compilation**: Compile via `tcompile` followed by `tbuild -cf <JarName>.jar`.
4. **Registration**: Ensure routine is cataloged in `PGM.FILE` (`TYPE = S`) and registered in `EB.API`."""
