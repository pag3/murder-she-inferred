"""Shared test helpers and sample transcripts."""

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

# A continuous-text transcript with site-generated header and footer.
WEBTEXT_TRANSCRIPT = (
    "Transcript Archive \u2022 01x04 - Birds of a Feather "
    "Transcript Archive "
    "Sample television and movie transcripts for testing and research. "
    "https://example.invalid/transcripts/ "
    "01x04 - Birds of a Feather "
    "https://example.invalid/transcripts/01x04-birds-of-a-feather "
    "Page 1 of 1 "
    "01x04 - Birds of a Feather "
    "Posted: 07/29/22 18:10 by bunniefuu "
    "I'm not particularly proud of what I had to do to earn that money, "
    "but I did it. And I want what's coming to me. Don't ever touch me "
    "like that again. You don't seem exactly broken up over Drake's death. "
    "Tell you what. I'll split a bouquet with you. If I love him, how can "
    "I justify spying on him? For your own peace of mind. No reasonable "
    "person could assume for one moment that I had anything to do with "
    "AI's death. No. Other than the fact that you despised the man. "
    "Catch that killer! [Birds Squawking] Mr. Drake. What do you say, "
    "kid? Out for some early morning air? I've gotta talk to ya. So talk. "
    "I need my money. We already had that conversation. You'll get it when "
    "you're finished. I'm finished. Come on now, kid. We got a deal. "
    "You're in it till I say otherwise. Now, look. You listen to me. "
    "I'm not particularly proud of what I had to do to earn that money, "
    "but I did it. And I want what's comin' to me. You're a nice kid, "
    "Howard, but don't you ever touch me like that again. Tonight, you be "
    "there, or you don't see a dime, you got that? Fritz. [Barks Fiercely] "
    "Come on, Fritz. You know, Al, too much of that stuff can give you a "
    "heart attack. You worried about me, Mike, or just fantasizing? "
    "I thought we had a deal. We do. Just be patient. Yeah, well, I've "
    "been patient for about six months. I think you're jerkin' my string, "
    "Al, that's what I think. Have you raised the money? Now, that's my "
    "problem, isn't it? Don't push me, Mike. Things are goin' real good "
    "right now. But I can live without you. Yeah? Well, speaking of living, "
    "anybody can live without anybody. [Barks] Fritz. [Growls Fiercely] "
    "[Whimpers] Actually, it's going to be a very simple wedding, intimate. "
    "Intimate. I see. Well, we can still make it very festive. "
    "All times are UTC-05:00"
    "Page 1 of 1 "
    "Powered by Example Forum Software \u00a9 Example Archive"
)


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


@pytest.fixture
def webtext_transcript_text():
    """Return a continuous-text transcript with boilerplate as a string."""
    return WEBTEXT_TRANSCRIPT


@pytest.fixture
def webtext_transcript_file(tmp_path):
    """Write the continuous-text transcript to a temp file and return the path."""
    path = tmp_path / "01x04_birds_of_a_feather.txt"
    path.write_text(WEBTEXT_TRANSCRIPT, encoding="utf-8")
    return path


@pytest.fixture
def synthetic_test_transcripts_dir() -> Path:
    """Return the committed directory of synthetic test-transcripts."""
    return Path(__file__).resolve().parents[1] / "test-run" / "01-transcripts"
