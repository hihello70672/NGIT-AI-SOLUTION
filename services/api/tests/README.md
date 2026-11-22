# API security tests

Run from the repository root with Python 3.10 or newer:

```sh
PYTHONPATH=services/api python -m unittest discover -s services/api/tests -v
```

The suite exercises opaque bearer-token lifecycle, expiry/revocation, role and
owner checks, approval separation/binding/one-time use, restricted action and
emergency-stop enforcement, audit redaction, and the safe error envelope. It
uses only the Python standard library and requires no external AI provider.
