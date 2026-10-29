import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from scripts import update_stats as stats


def repo(id=1, **overrides):
    return dict({"id": id, "fork": False, "private": False,
                 "owner": {"login": stats.USERNAME}, "language": "Python",
                 "stargazers_count": 3, "forks_count": 2}, **overrides)


class StatsTests(unittest.TestCase):
    @patch.object(stats, "github", return_value={"total_count": 235, "incomplete_results": False})
    def test_commit_query_uses_author_public_scope_and_2026_dates(self, github):
        result = stats.fetch_commits("2026-10-29")
        self.assertEqual(result["count"], 235)
        self.assertEqual(result["year"], 2026)
        query = parse_qs(urlparse(github.call_args.args[0]).query)
        self.assertEqual(query["q"], ["author:AntonioMelgarMendez is:public author-date:2026-01-01..2026-10-29"])
        self.assertEqual(query["per_page"], ["1"])

    @patch.object(stats, "github", return_value={"total_count": 0, "incomplete_results": False})
    def test_commit_query_caps_at_year_end_and_accepts_zero(self, github):
        result = stats.fetch_commits("2027-02-01")
        self.assertEqual(result["through"], "2026-12-31")
        self.assertEqual(result["count"], 0)

    @patch.object(stats, "github")
    def test_bad_or_incomplete_commits_are_not_published(self, github):
        for response in ({"total_count": 10, "incomplete_results": True},
                         {"total_count": 10}, {"total_count": -1, "incomplete_results": False},
                         {"total_count": "10", "incomplete_results": False},
                         {"total_count": True, "incomplete_results": False}):
            github.return_value = response
            with self.subTest(response=response), self.assertRaises(ValueError):
                stats.fetch_commits("2026-10-29")

    @patch.object(stats, "github")
    def test_commit_date_before_2026_is_rejected(self, github):
        with self.assertRaises(ValueError):
            stats.fetch_commits("2025-12-31")
        github.assert_not_called()

    @patch.object(stats, "write_assets")
    @patch.object(stats, "fetch_commits", side_effect=ValueError("incomplete"))
    @patch.object(stats, "fetch_repositories", return_value=[])
    @patch.object(stats, "github", return_value={"followers": 4})
    def test_commit_failure_preserves_previous_snapshot(self, github, repos, commits, write):
        with self.assertRaises(ValueError):
            stats.main()
        write.assert_not_called()

    def test_commit_card_does_not_turn_unknown_count_into_zero(self):
        data = stats.summarize({"followers": 0}, [], "2026-10-29")
        self.assertIn("-- public authored commits", stats.stats_card(data))
        data["commits"] = {"count": 235, "year": 2026}
        self.assertIn("235 public authored commits in 2026", stats.stats_card(data))

    def test_only_original_public_owned_repositories_are_counted(self):
        data = stats.summarize({"followers": 4}, [repo(), repo(), repo(2, fork=True),
                               repo(3, private=True), repo(4, owner={"login": "another-owner"}),
                               repo(5, language=None)], "2026-10-29")
        self.assertEqual((data["repositories"], data["stars"], data["forks"], data["followers"]),
                         (2, 6, 4, 4))
        self.assertEqual(data["languages"], {"Python": 1})

    def test_owner_matching_is_case_insensitive(self):
        data = stats.summarize({"followers": 0}, [repo(owner={"login": stats.USERNAME.lower()})], "today")
        self.assertEqual(data["repositories"], 1)

    @patch.object(stats, "github")
    def test_all_repository_pages_are_loaded(self, github):
        github.side_effect = [[repo(i) for i in range(100)], [repo(100)]]
        self.assertEqual(len(stats.fetch_repositories()), 101)
        self.assertIn("page=2", github.call_args.args[0])

    @patch.object(stats, "github", return_value={"message": "error"})
    def test_bad_repository_response_fails(self, github):
        with self.assertRaises(ValueError):
            stats.fetch_repositories()

    def test_language_grouping_keeps_total_and_max_six_rows(self):
        languages = {f"Language {i}": i + 1 for i in range(10)}
        rows = stats.language_rows(languages)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1][0], "Other")
        self.assertEqual(sum(n for _, n in rows), sum(languages.values()))

    def test_exactly_six_languages_are_not_grouped(self):
        self.assertEqual(len(stats.language_rows({str(i): 1 for i in range(6)})), 6)
        self.assertNotIn("Other", dict(stats.language_rows({str(i): 1 for i in range(6)})))

    def test_empty_profile_and_svg_escaping(self):
        data = stats.summarize({"followers": 0}, [], "2026-10-29")
        self.assertEqual(data["repositories"], 0)
        self.assertIn("No public language data", stats.language_card(data))
        data["languages"] = {"<script>&Ruby": 1}
        for svg in (stats.stats_card(data), stats.language_card(data)):
            ET.fromstring(svg)
            self.assertNotIn("<script>", svg)

    def test_snapshot_and_cards_are_written(self):
        data = stats.summarize({"followers": 4}, [repo()], "2026-10-29")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            stats.write_assets(data, destination)
            self.assertEqual(json.loads((destination / "stats.json").read_text()), data)
            self.assertEqual(len(list(destination.glob("*.svg"))), 2)
            for path in destination.glob("*.svg"):
                ET.parse(path)
            self.assertFalse(list(destination.glob("*.tmp")))

    @patch.object(stats, "write_assets")
    @patch.object(stats, "github", side_effect=URLError("offline"))
    def test_api_failure_does_not_overwrite_cards(self, github, write):
        with self.assertRaises(URLError):
            stats.main()
        write.assert_not_called()

    @patch.object(stats, "write_assets")
    @patch.object(stats, "fetch_repositories", side_effect=URLError("offline"))
    @patch.object(stats, "github", return_value={"followers": 4})
    def test_partial_fetch_failure_does_not_overwrite_cards(self, github, repos, write):
        with self.assertRaises(URLError):
            stats.main()
        write.assert_not_called()

    @patch.object(stats.time, "sleep")
    @patch.object(stats, "urlopen", side_effect=HTTPError("https://api.github.com", 503, "unavailable", {}, None))
    def test_transient_errors_retry_three_times(self, request, sleep):
        with self.assertRaises(HTTPError):
            stats.github("/users/test")
        self.assertEqual(request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch.object(stats, "urlopen", side_effect=HTTPError("https://api.github.com", 403, "forbidden", {}, None))
    def test_non_transient_errors_fail_immediately(self, request):
        with self.assertRaises(HTTPError):
            stats.github("/users/test")
        self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
