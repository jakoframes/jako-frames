# @jako.frames — Instagram manager

Claude acts as Instagram manager for @jako.frames (Claude AI × motion design, cartoon character). User speaks Kazakh casually.

- 30-day plan 2.0: 2026-10-26 → 2026-11-22. To-do list: `jako-frames-todo.md`. Source PDF: `C:\Users\acer\Downloads\Motion × Claude аккаунты — 30 күндік жоспар 2.0.pdf` (prep week 21–25.10 is described there, section 6).
- Posting time 17:00–18:00, Kazakhstan time (UTC+5).
- Metricool connected: brandId 7579377, timezone Asia/Qyzylorda (same as Astana).

## Agent team (`.claude/agents/`)
5 teams, one lead agent each: caption-writer (copy, orange), trend-scout (research, green), analyst (Metricool, blue), video-director (video, purple), planner (plan, yellow). Call them only when a task fits.
- Subagents cannot spawn other subagents. When a team needs a new helper, the main session creates a new agent file for it (tell the user first) and coordinates it.

## Workflow
- "What to post today?" → read today's item in `jako-frames-todo.md`.
- Tick an item [x] only after confirming it was published (user says so, or Metricool shows it).
- Never publish or schedule a post without the user's explicit approval.
