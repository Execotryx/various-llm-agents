# System prompt extraction

Date: 2026-07-18

## Changes

- Moved the business-idea investigator system behavior into a Markdown prompt file owned by the OpenAI example.
- Moved the tweet generator's generation, reflection, and revision system prompts into separate Markdown files owned by the tweet-generator package.
- Added module-relative UTF-8 prompt loading so prompt resolution does not depend on the process working directory or launch mode.
- Documented the external prompt locations in the repository guidance.

## Reasoning

Keeping system prompts outside Python makes them easier to review and revise as prose while retaining explicit ownership by each independent example area. Module-relative paths preserve the existing direct-script and package-module launch modes.
