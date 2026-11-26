import pytest

from src.monitoring import ConfidenceMonitor, ConfidenceZone, MonitoringConfig, load_config


def config(lower=0.60, upper=0.80):
    return MonitoringConfig(
        version="monitoring-v1",
        lower_threshold=lower,
        upper_threshold=upper,
        window_size=20,
        minimum_observations=10,
        default_source_id="local-image",
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.40, ConfidenceZone.LOW_CONFIDENCE),
        (0.59, ConfidenceZone.LOW_CONFIDENCE),
        (0.599, ConfidenceZone.LOW_CONFIDENCE),
        (0.60, ConfidenceZone.UNCERTAIN),
        (0.75, ConfidenceZone.UNCERTAIN),
        (0.79, ConfidenceZone.UNCERTAIN),
        (0.799, ConfidenceZone.UNCERTAIN),
        (0.80, ConfidenceZone.ACCEPTED_BY_POLICY),
        (0.95, ConfidenceZone.ACCEPTED_BY_POLICY),
        (None, ConfidenceZone.NO_DETECTION),
    ],
)
def test_confidence_boundaries(score, expected):
    assert ConfidenceMonitor(config()).classify(score) == expected


@pytest.mark.parametrize("lower,upper", [(-0.01, 0.8), (0.8, 0.8), (0.9, 0.8), (0.6, 1.01)])
def test_invalid_thresholds_fail(lower, upper):
    with pytest.raises(ValueError, match="lower_threshold < upper_threshold"):
        config(lower, upper)


def test_invalid_yaml_configuration_fails_with_clear_message(tmp_path):
    path = tmp_path / "monitoring.yaml"
    path.write_text(
        "config: {version: monitoring-v1}\n"
        "confidence: {lower_threshold: 0.80, upper_threshold: 0.60}\n"
        "monitoring: {window_size: 20, minimum_observations: 10}\n"
        "source: {default_id: local-image}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="configuración de monitoreo inválida"):
        load_config(path)
