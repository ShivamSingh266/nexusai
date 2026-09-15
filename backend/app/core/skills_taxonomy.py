# OWNER: Member 4
# Canonical skills taxonomy + alias resolution.
# Populates: models.Skill (id, canonical_name, category, aliases, source, version)
# Contract expected by Member 5's matcher (app/core/matching.py::_skill_coverage):
#   every candidate_skills/job_skills/role_skills row must reference the
#   canonical skill_id — resolve aliases HERE, before writing those rows,
#   not downstream. See docs/CONTRACT_member4_skills.md.
