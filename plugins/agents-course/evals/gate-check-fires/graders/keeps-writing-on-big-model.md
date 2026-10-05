---
type: llm
---

PASS if the reply proposes gates only for the bounded decisions (spam, queue,
needs-a-human) and leaves the reply writing on the large model.
FAIL if it proposes replacing the large model for writing the replies, or
proposes no cheaper layer for any of the decisions.
