# jira-stories

Meridian National Bank IAM backlog for Claude Code intake.

| Path | Purpose |
| --- | --- |
| `MNB-IAM-backlog.md` | Human-readable 25 stories + acceptance/MCP/lab maps |
| `MNB-IAM-backlog.csv` | Jira CSV import (Status = To Do) |
| `fixtures/*.json` | Offline poller / `/work` without live Jira |

## Poll fixtures

```bash
python3 scripts/jira/todo_poll.py --all --fixture jira-stories/fixtures
```
