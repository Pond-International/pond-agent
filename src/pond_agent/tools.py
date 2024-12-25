import os
import subprocess


def run_python_script(script_path: str, env: dict = None, logger = None) -> None:
    """Run Python script.

    Args:
        script_path: Path to Python script

    """
    if env is None:
        env = os.environ.copy()

    process = subprocess.Popen(  # noqa: S603
        ["python", str(script_path)],  # noqa: S607
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line-buffered output
    )
    for line in process.stdout:
        if logger:
            logger.info(line.rstrip("\n"))
        else:
            print(line.rstrip("\n"))

    process.stdout.close()
    returncode = process.wait()

    # Read any remaining stderr output
    stderr = process.stderr.read()
    process.stderr.close()

    return returncode, stderr
