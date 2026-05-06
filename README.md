# Creator Content Posting Optimization System

## Team Information
- **Team Name**: BGH Squad
- **Year**: 2nd Year
- **All-Female Team**: Yes

## Architecture Overview

## Architecture Overview

Our system pre-computes the best (platform, time_slot) for every (creator_id, content_type) combination at startup using O(1) hash-map lookups, reducing per-item recommendation to a single dict lookup. Score mirrors the eval formula: 0.50×(base×activity×history) + 0.20×activity + 0.15×platform_quality. Dual-platform is recommended when both scores are within 2% of each other. POST_NOW triggers when optimal slot matches created_timestamp hour, else SCHEDULE. All tie-breaking is deterministic (Instagram-first, lower-slot-first). Precomputation covers 50 creators × 2 types × 2 platforms × 24 slots = 4,800 operations once; 1,200 items then resolve in O(N).

---

*Keep your description concise and focused on your core decision-making logic.*

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.