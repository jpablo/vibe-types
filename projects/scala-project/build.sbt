// Reference build for strongly typed functional Scala 3 projects.
//
// This project serves two purposes:
//   1. Reference environment — the compiler settings and library choices below
//      are the recommended baseline for new strongly-typed FP projects.
//   2. Snippet verification — the verify-markdown-snippets skill compiles every
//      ```scala fence in the docs against this project's Scala version and
//      dependencies (see plugin/skills/verify-markdown-snippets/scripts/verify_scala.py,
//      which parses `scalaVersion` and `libraryDependencies` out of this file).

val scala3Version = "3.8.4"

lazy val root = project
  .in(file("."))
  .settings(
    name := "scala-project",
    version := "0.1.0",
    scalaVersion := scala3Version,

    scalacOptions ++= Seq(
      // --- Correctness ---------------------------------------------------
      "-deprecation",        // warn on use of deprecated APIs
      "-feature",            // warn on use of features that require an explicit language import
      "-unchecked",          // detail where generated code relies on unchecked assumptions
      "-Wsafe-init",         // flag fields read before initialization (object init safety)
      "-Wvalue-discard",     // warn when a non-Unit result is silently discarded
      "-Wnonunit-statement", // warn when a non-Unit expression is used as a statement
      "-Wunused:all",        // unused imports, locals, privates, params — keep the code honest
      // --- Style -----------------------------------------------------------
      "-new-syntax",         // require `if x then y` over `if (x) y`; no paren-style control flow
      // --- Strictness --------------------------------------------------------
      "-Werror",             // warnings are errors. Doc snippets are compiled with a relaxed
                             // subset instead — see verify_scala.py — so docs don't need
                             // to be warning-free, but in-tree code does.
      // --- Optional hardening — enable per-project as the team is ready -----
      // "-source:future",           // opt in to next-version semantics early
      // "-language:strictEquality", // require CanEqual evidence for == / != (see T20-equality-safety)
      // "-Yexplicit-nulls",         // Java results become `T | Null`; null must be handled (see T13-null-safety)
    ),

    libraryDependencies ++= Seq(
      // Snippet-verification dependencies: catalog entries that center on a
      // specific ecosystem library (cats for T54/T55, iron for T26, zio/cats-effect
      // for T12/T56) are verified against the real artifact.
      "org.typelevel"      %% "cats-core"   % "2.13.0",
      "org.typelevel"      %% "cats-effect" % "3.7.0",
      "dev.zio"            %% "zio"         % "2.1.26",
      "io.github.iltotore" %% "iron"        % "3.3.1",
      "org.scalameta"      %% "munit"       % "1.3.3" % Test,
    ),
  )
