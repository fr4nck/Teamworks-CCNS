from __future__ import annotations

from CcnsCore.runtime_bridge import summary


if __name__ == "__main__":
    resume = summary()
    print("=== Teamworks-CCNS bridge demo ===")
    for key, value in resume.items():
        print(f"- {key}: {value}")
