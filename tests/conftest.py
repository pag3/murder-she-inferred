"""Shared test fixtures."""

import pytest
from pathlib import Path


SAMPLE_TRANSCRIPT = """\
FADE IN:

INT. CABOT COVE - JESSICA'S HOUSE - MORNING

Jessica Fletcher sits at her typewriter, working on her latest novel.
The phone rings.

JESSICA: Hello? Oh, Sheriff Metzger... A body? At the marina?

INT. CABOT COVE MARINA - DAY

Jessica arrives at the marina. Sheriff Metzger stands near the dock.
A body lies covered by a tarp.

METZGER: It's Tom Kingsley. Found him this morning.
JESSICA: Tom? But I just saw him at the charity dinner last night.

Tom's business partner RICHARD COLE approaches nervously.

RICHARD: What happened? Is Tom...?
METZGER: I'm afraid so. When did you last see him?
RICHARD: Last night. We argued about selling the business. He wanted out.

HELEN KINGSLEY, Tom's wife, arrives in tears.

HELEN: Oh no, Tom! Who did this?
JESSICA: Helen, I'm so sorry. Did Tom mention any concerns recently?
HELEN: He said someone was threatening him. He wouldn't say who.

INT. CABOT COVE - SHERIFF'S OFFICE - DAY

Jessica and Metzger review the evidence.

METZGER: The coroner says poison. Administered sometime after midnight.
JESSICA: Richard had motive — the business dispute. And Helen inherits everything.
METZGER: Don't forget FRANK BUTLER. He owed Tom a fortune in gambling debts.

EXT. CABOT COVE - BUTLER'S HOUSE - DAY

Jessica visits Frank Butler.

FRANK: I didn't kill Tom. Sure, I owed him money, but I was paying it back.
JESSICA: Can anyone confirm where you were last night?
FRANK: I was at the bar until 2 AM. Ask the bartender.

INT. CABOT COVE - JESSICA'S HOUSE - EVENING

Jessica reviews her notes.

JESSICA (V.O.): Frank's alibi checks out. The bartender confirmed he was there all night.
That rules him out. But Richard's story has holes...

INT. CABOT COVE MARINA - NIGHT (FLASHBACK)

Jessica imagines the scene.

JESSICA (V.O.): Richard said they argued about selling. But Tom's lawyer told me
the partnership agreement had a life insurance clause. If one partner dies...

INT. CABOT COVE - SHERIFF'S OFFICE - DAY

JESSICA: Sheriff, I think I know who did it. Richard Cole had the most to gain.
The insurance clause in their partnership pays out double in case of death.
And Richard's alibi for after midnight doesn't hold up.
METZGER: I'll bring him in.

FADE OUT.
"""


@pytest.fixture
def sample_transcript_text():
    """Return the sample transcript as a string."""
    return SAMPLE_TRANSCRIPT


@pytest.fixture
def sample_transcript_file(tmp_path):
    """Write the sample transcript to a temp file and return the path."""
    path = tmp_path / "s01e01_the_murder_of_sherlock_holmes.txt"
    path.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    return path
