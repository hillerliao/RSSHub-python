---
name: Update delimiter documentation
overview: Add documentation for custom delimiter support in the /randomline parameter description in feeds.html.
todos:
  - id: locate-feeds-file
    content: Use [subagent:code-explorer] to locate feeds.html and examine current /randomline documentation
    status: completed
  - id: update-delimiter-doc
    content: Add custom delimiter documentation to /randomline parameter description in feeds.html
    status: completed
    dependencies:
      - locate-feeds-file
---

## Product Overview

Update the documentation for the /randomline parameter in feeds.html to include information about custom delimiter support.

## Core Features

- Add documentation explaining that custom delimiters (e.g., "---", "***") are supported
- Update the parameter description in feeds.html template to reflect existing implementation capabilities

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: Locate and examine the feeds.html file to understand the current documentation structure
- Expected outcome: Identify the exact location and context of the /randomline parameter documentation that needs updating