# jobsworth

*Expiring exceptions for Trivy and Checkov audits.*

Jobsworth is a proposed **Python 3.14** CLI that preserves native scanner evidence and evaluates local and centrally managed, scoped, time-limited exceptions. **The repository currently contains a scaffold, not an implemented audit CLI.**

Trivy will inspect Rust, Python, Go, Bun, npm, and pnpm dependency inputs. Checkov will inspect selected Terraform, Ansible, and GitHub Actions configuration rules. Workflow checks do not establish coverage of third-party action dependencies; Terraform provider and Ansible Galaxy advisories remain separate.

## Development

```bash
git clone https://github.com/leynos/jobsworth.git
cd jobsworth
uv sync --locked --group dev
uv run --locked python -c "from jobsworth import hello; print(hello())"
```

The greeting tests only the scaffold. Existing quality gates remain in place.

## Documentation

- [Terms of reference](docs/terms-of-reference.md)
- [Technical design](docs/jobsworth-design.md)
- [GIST roadmap](docs/roadmap.md)
- [ADR 0001](docs/adrs/adr-0001-scanner-and-policy-boundary.md)
- [Documentation contents](docs/contents.md)

ISC licence; see [LICENSE](LICENSE).
