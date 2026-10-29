# Profile maintenance

## Local live preview

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-preview.txt
.venv/bin/python scripts/preview.py
```

Open **http://127.0.0.1:4173**. Changes to `README.md` and files in `assets/` reload automatically. The preview includes dark/light modes and responsive layouts. It approximates GitHub's Markdown styling; it is not a separate portfolio website. All profile visuals are local PNG/SVG assets with accessible alternative text.

## Update the statistics

```sh
python3 scripts/update_stats.py
python3 -m unittest discover -s tests -v
```

The generator uses only Python's standard library and GitHub's REST API. It works without a token locally (subject to public API rate limits); an optional `GITHUB_TOKEN` increases the rate limit. Never paste tokens into files or commit them.

- **Repository/language scope:** original, public repositories owned by `AntonioMelgarMendez`; forks, private repositories, and organization-owned work are excluded from these metrics.
- **Commits 2026:** GitHub Search Commits `total_count` for `author:AntonioMelgarMendez is:public author-date:2026-01-01..YYYY-MM-DD`. The cutoff is the UTC refresh date, capped at December 31, 2026. Includes indexed public commits by this author, including public organization repositories; search covers default branches only. This is not the contribution-calendar total, not all branches, and not private commits. A personal token does not silently broaden this metric: `is:public` is always enforced. Missing or incomplete search results abort the update, preserving the previous snapshot. [GitHub commit search semantics](https://docs.github.com/en/search-github/searching-on-github/searching-commits).
- **Stats:** repository count, stars earned, forks received, and public profile followers.
- **Languages:** each repository contributes once to its GitHub-detected primary language. This is a **repository distribution**, not bytes, lines of code, skill level, or all-time contributions. Repositories with no language are excluded. More than six languages are condensed into five plus Other.
- **Resilience:** API requests complete before any assets are replaced. A failed fetch leaves the last successful cards intact. Each card has a UTC refresh date. `assets/stats.json` is the inspectable source snapshot.

## Enable automatic refresh on GitHub

1. Commit and push the README, assets, generator, tests, and workflow to `main`.
2. Open **Actions → Update profile stats → Run workflow** to verify the first run. The initial push also triggers it when the workflow/generator files change.
3. The workflow runs daily at **09:23 UTC** with the built-in `GITHUB_TOKEN`; no personal access token or external stats hosting is required.
4. If repository/organization policies or branch protection block the bot's commit, allow this workflow to write to the target branch or adapt it to open a pull request instead. Do not disable branch protection blindly.

GitHub can delay scheduled workflows and disables schedules in public repositories after 60 days without activity. If updates stop, check the last workflow run and re-enable the schedule in Actions. Existing images remain available regardless.

References: [GitHub REST repositories](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user), [scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [why the previous public stats service can be unreliable](https://github.com/anuraghazra/github-readme-stats#important-notices).

## Edit the design

- `README.md`: profile copy, links, projects, and section order.
- `assets/pixel-workspace.png`: original pixel-art illustration; source prompt and provenance in [ART-DIRECTION.md](./ART-DIRECTION.md).
- `scripts/pixel_art.py`: original 5×7 alphabet rendered as SVG paths, not external fonts.
- `scripts/build_pixel_assets.py`: regenerates the pixel masthead, section labels, buttons, and stack symbols (`python3 scripts/build_pixel_assets.py`).
- `assets/pixel-*.svg` / `heading-*.svg`: generated static pixel UI.
- `scripts/update_stats.py`: stats card rendering and public-data aggregation.

The stats generator imports `scripts/pixel_art.py`; keep both files when publishing. The snapshot data and update semantics are unchanged by the pixel-art redesign.

The README intentionally uses GitHub-compatible HTML and Markdown, not custom CSS or JavaScript. CSS and JavaScript are used **only in the local preview**, never in the profile itself.
