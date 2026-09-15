# OWNER: Member 6
# Demand forecasting -> models.SkillForecast (trend, forecast, model_version).
# Contract expected by Member 5's gap analyzer (app/core/gap.py::_trend_multiplier):
#   `trend` is a MULTIPLIER (e.g. 1.3 = growing 30%), not a raw score.
