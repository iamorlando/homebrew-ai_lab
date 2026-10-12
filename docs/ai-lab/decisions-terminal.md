# Decisions

The terminal Decisions app was removed in 0.1.15. Run `ai-lab web` and open
**Decisions** for the existing Ask/Rank interface. Choose native CLM or Jev.
Launching the website starts both CLM and DeepSeek APIs and keeps them running
until the web process exits. Jev uses `TYPESAFE_API_KEY` or `JEV_API_KEY`.
