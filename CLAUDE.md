# jellyfin-plugins

Repositório de plugins do Jellyfin do Angelo (só o catálogo). Responda em português do Brasil. Público: nada de
segredos ou detalhes da VPS. Operação no `~/ops/CLAUDE.md`; decisões no `~/ops/plano-jellyfin-personalizacao.md`.

- `manifest.json` é **gerado**: não editar à mão. `generate.py` lê os releases dos repositórios de `plugins.json`
  (um zip por release, com `meta.json` dentro) e reaproveita os checksums já conhecidos.
- O workflow `Update manifest` roda de hora em hora e sob demanda, com o `GITHUB_TOKEN` (sem token pessoal). Depois de
  publicar uma versão: `gh workflow run manifest.yml -R ApenasAngelo/jellyfin-plugins`. O GitHub desliga agendas de
  repositórios sem atividade há 60 dias: se parar, rodar à mão ou reativar em Actions.
- Rodar localmente: `GH_TOKEN=$(gh auth token) python3 -I generate.py`.
- Plugin novo: uma linha em `plugins.json` (repo e `imageUrl`) e, no repositório dele, o mesmo workflow de release
  dos outros (`meta.json` modelo + tag `vX.Y.Z.W` anotada com o changelog).
- Commits em inglês (Conventional Commits).
