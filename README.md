# Creator Content Posting Optimization System

## Team Information
- **Team Name**: BGH Squad
- **Year**: 2nd Year
- **All-Female Team**: Yes

## Architecture Overview

Our system loads all four CSVs into memory using dictionary lookups for O(1) access. For each content item, we jointly optimize platform and time slot by computing a weighted engagement score: base_engagement × activity_score × avg_engagement with a soft platform quality bias (SHORT→Instagram=1.0, LONG→YouTube=1.0). We select the globally optimal (platform, time_slot) pair and decide POST_NOW if the optimal slot matches submission time, else SCHEDULE. This ensures deterministic, fast recommendations that maximize engagement while respecting content-type and platform affinity signals.

---

*Keep your description concise and focused on your core decision-making logic.*

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.