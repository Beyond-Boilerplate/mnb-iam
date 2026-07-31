Connect JIRA to claude
> claude mcp add --scope user --transport sse jira https://mcp.atlassian.com/v1/sse
> claude 
> /mcp -> select the jira mcp and enable + authenticate
> give me a title of 1 story that is in todo column -> test the connection

Create a statusline
> cd ~/.claude && touch statusliine.sh
> chmod +x ~/.claude/statusline.sh
> add the below block to ~/.claude/settings.json
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2,
    "refreshInterval": 5
  },
  "hideVimModeIndicator": true
}
```

Daily Usage
> shift + tab --> toggle claude modes

> /init --> create project's claude.md file

Diagnosis
> Ctrl+E  -> to show an explanation of the command: what it does, why Claude is running it, and what could go wrong, labeled Low risk, Med risk, or High risk