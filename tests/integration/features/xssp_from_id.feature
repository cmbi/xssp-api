Feature: XSSP entries
  As a structural bioinformatician
  I want to inspect existing XSSP entries via XSSP-API

  Scenario Outline: request XSSP entry via XSSP-API
    Given the list of existing "<xssp>" entries
    When we request an existing "<output format>" entry
    Then the status should be "SUCCESS"

    Examples: xssp type and format combi's
        | xssp              | output format  |
        | DSSP_PRESENT      | dssp           |
        | DSSP_REDO_PRESENT | dssp           |
        | HSSP_PRESENT      | hssp_hssp      |
        | HSSP_PRESENT      | hssp_stockholm |
