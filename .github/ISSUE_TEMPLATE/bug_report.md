---
name: Bug report
about: Report a reproducible problem with a minimal synthetic example.
---

Share only minimal synthetic examples. Do not include API keys, tokens,
passwords, private paths, authenticated URLs, private prompts, private
workflows, or private assets. A clean CWA report does not guarantee the
absence of secrets.

If a detail is not known, write "unknown". Do not include machine names,
usernames, machine identifiers, or a full system inventory.

## 1. Version and environment

- CWA version or commit:
- Python version:
- Operating system family and version:

## 2. Format and parameters

- Format: generic-json / auto / workflow-v1 / workflow-v0.4 / api / unknown
- Command or parameters used (replace all real paths, including interpreter,
  input/output, redirection and other argument paths, with placeholders such
  as `python`, `sample.json` or `report.json`):

Example command shape; replace the format and options with those actually used:

```text
python -S -m workflow_auditor audit sample.json --format auto --output-format json
```

## 3. Steps to reproduce

1.
2.
3.

## 4. Expected and actual result

- Expected result:
- Actual result (brief description and non-sensitive CWA rule IDs, if available):
- Observed exit code: <exact number, or `unknown` if not captured>
- Code reported by (if known): CWA/Python process / shell or launcher / unknown

CWA documents exit codes 0, 1, 2 and 3. Report any other observed value
unchanged. A number alone does not establish that CWA produced a diagnostic.

Do not paste complete terminal histories or full logs.
Include only the smallest relevant excerpt after removing private data.
If it cannot be shared safely, describe the symptom instead.

## 5. Minimal synthetic sample

Provide the smallest synthetic JSON sample that reproduces the problem.
If one is not yet available, write "unknown". Do not attach the original
private workflow, prompts, or creative assets.
