# Profile maintenance

The profile README uses repository-local SVG assets. There is no external
statistics image service to go down, and no personal access token is required.

## Refreshing the statistics

`Refresh profile statistics` runs once a day at 05:17 UTC (08:17 in Türkiye).
You can also run it manually from **Actions → Refresh profile statistics → Run workflow**.
GitHub may delay scheduled jobs or disable inactive schedules after 60 days.

The workflow uses the repository's temporary `GITHUB_TOKEN` with `contents: write`
to commit the two statistics cards and their public aggregate data.

Only public repositories owned by TheDarkGuardian are included. Forks, disabled
repositories and this profile repository are excluded. Archived public projects
remain included. Percentages use the GitHub languages API's code-byte totals;
they do not measure expertise, time or authorship of every line. The ten-row
chart groups the smallest languages as Other when needed. All totals are kept
in `assets/stats.json`.

To update locally with Python 3.10+ and an authenticated GitHub CLI:

```sh
python scripts/generate_stats.py
```

The technology badges are a curated list, separate from automatic percentages.
PHP is included at the profile owner's request; it was not present in the
public repository language data checked on 6 November 2026. C# is used in Dispatch.
Other badges were checked against public code, manifests and project documentation.

## Artwork

Banner and statistic card layouts were created for this profile. The downloaded
technology badges come from [Shields.io](https://shields.io/) using
[Simple Icons](https://simpleicons.org/). The C# badge uses the .NET logo.
The CSS3 badge uses the current CSS logo.
