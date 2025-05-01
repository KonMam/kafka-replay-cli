import subprocess


def test_version_output():
    result = subprocess.run(["python", "-m", "kafka_replay_cli.cli", "version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "kafka-replay-cli version" in result.stdout
