# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in behave-gen, please report it
responsibly.

- Email: **mathias@paulenko.dev**
- Do not open a public GitHub issue for security vulnerabilities.

## Response time

We aim to acknowledge reported vulnerabilities within **48 hours** and to
provide a fix or mitigation according to severity.

## Scope

behave-gen is a CLI scaffolding and code generation tool. It reads OpenAPI,
Postman, and Swagger specs, writes `.feature` files and Python step
definitions, and may invoke ecosystem tools (behave-doctor, behave-lint,
behave-format) as subprocesses. Vulnerabilities related to parsing untrusted
spec files, template injection, or arbitrary code execution via generated
output are in scope.
