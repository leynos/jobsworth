Feature: Refresh shared reference documentation
  Existing shared documents follow the reference library while project-specific
  documents remain local.

  Scenario: Refresh only existing reference documents
    Given a documentation directory with a shared guide and a project guide
    When the refresh command downloads the latest reference archive
    Then only the shared guide is replaced and the update is reported
