# Environments

This folder will contain MuJoCo XML scene definitions (`.xml`) and Isaac Lab environment configs (`.py`) as the sim layer grows.

For MVP, the replay engine runs pure geometry checks using the scenario JSON files in `../scenarios/`.
When physics fidelity becomes critical, drop a MuJoCo `.xml` here and update `engine.py` to load it with `mujoco.MjModel.from_xml_path()`.
