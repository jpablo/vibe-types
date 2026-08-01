#!/usr/bin/env python3
"""Print the scala-cli flags the doc-snippet checker uses, for ad-hoc probes.

Ad-hoc `scala-cli` invocations do not inherit anything from the reference sbt
project (scala-cli does not read build.sbt, and a `project.scala` only applies
to directory inputs). Hand-typing `--scala`/`--dep` therefore risks probing a
different compiler or dependency set than the one the docs are verified against.

This emits exactly the flags verify_scala.py builds -- same Scala version, same
dependencies, same relaxed scalac options -- so `make scala-probe` and the
snippet checker agree by construction. build.sbt stays the single source of truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_scala as vs

cfg = vs.parse_build_sbt()
if cfg.get("scala_version") is None:
    sys.exit("could not parse scalaVersion from build.sbt")

flags = ["--scala", cfg["scala_version"]]
for dep in cfg["dependencies"]:
    flags += ["--dep", dep]
for opt in vs.SNIPPET_SCALAC_OPTIONS:
    flags += ["-O", opt]
print(" ".join(flags))
