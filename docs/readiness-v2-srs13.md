# Readiness v2 — SRS 1.3

POST `/api/v1/readiness` is service-authenticated. Existing skill-gap and
skill-match endpoints retain v1 semantics for compatibility and replay.

Version: `readiness-v2-srs13`. Policy: `readiness-policy-srs13-v1`.

Skill Match is the importance-weighted mean of capped current/required ratios.
Required level zero is excluded; no required positive weight is rejected.
Duplicate skills, unknown fields, nonfinite values and invalid ranges are rejected.
Weights may be zero individually but available component weight must be positive.

Composite defaults: SM .65, PE .20, AR .10, PC .05. Null means unavailable;
zero means a measured zero. Available weights are renormalized. Unavailable
components produce a provisional result and explicit excluded names. Keep full
precision until the final two-decimal result. Compare critical ratios before
rounding: below .50 (strictly) caps final composite at 69, not Skill Match.
Only mark cap_applied when the cap reduces the score. Bands use the rounded final score.

Request includes the full actual policy values and optional component scores.
Backend freezes inputs and component provenance in DecisionSnapshot before calling
FastAPI. The returned policy and input component scores must match that snapshot.
Store actual policy and effective weights with the result, not only a version label.

Backend flag `DATA_SCIENCE_COMPOSITE_READINESS_ENABLED` defaults false. Deploy DS
first, verify the new endpoint, deploy Backend, then enable and recalculate a
controlled account. Both readiness/calculate and intelligence/calculate use the
same orchestration when enabled. No bulk historical recalculation or rewriting.
Rollback: disable the flag for new calculations; previous snapshots remain intact.

Current component adapters deliberately remain limited: PE uses the existing count
of completed accepted evaluated projects, not yet role relevance/difficulty/quality;
AR uses mean canonical evidence confidence only when every required skill has a
skill-confidence-v1 aggregator result. It never uses baseline answer coverage.
Otherwise AR is null. Baseline evidence aggregation is the next integration task.
PC uses configured approved fields and is unavailable when the field list is empty.
These adapters must not be presented as the final scientific validation of the SRS.

Run `python -m pytest tests/test_readiness_v2.py tests/test_skill_gap_api.py
tests/test_skill_match_service.py tests/test_service_token_auth.py -q`.
The first test contains the independent SRS worked example SM=85, readiness=81.75.
No participant data is required.
