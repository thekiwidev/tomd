from pathlib import Path

import pytest

import links

VIDEO = "_0A2BnRYVCo"


@pytest.mark.parametrize("url", [
    f"https://www.youtube.com/watch?v={VIDEO}",
    f"https://youtube.com/watch?v={VIDEO}&t=10s",
    f"https://m.youtube.com/watch?v={VIDEO}",
    f"https://youtu.be/{VIDEO}",
    f"https://youtu.be/{VIDEO}?si=abc",
])
def test_accepted_links_yield_the_video_id(url):
    assert links.parse_youtube_url(url) == (VIDEO, None)


@pytest.mark.parametrize("url, fragment", [
    (f"https://www.youtube.com/shorts/{VIDEO}", "Shorts"),
    (f"https://www.youtube.com/live/{VIDEO}", "Live stream"),
    (f"https://www.youtube.com/embed/{VIDEO}", "Embed"),
    ("https://www.youtube.com/playlist?list=PL123", "playlist"),
    ("https://www.youtube.com/channel/UC123", "channel"),
    ("https://www.youtube.com/watch?v=tooshort", "valid video id"),
    (f"youtu.be/{VIDEO}", "https://"),
    ("https://example.com/watch?v=" + VIDEO, "isn't a YouTube link"),
    ("https://music.youtube.com/watch?v=" + VIDEO, "isn't a video page"),
    ("https://www.youtube.com/watch", "doesn't name a video"),
])
def test_rejected_links_say_why(url, fragment):
    video_id, error = links.parse_youtube_url(url)
    assert video_id is None
    assert fragment in error


def test_empty_input_is_neither_valid_nor_an_error():
    assert links.parse_youtube_url("  ") == (None, None)


def test_canonical_url_is_the_shape_markitdown_recognises():
    assert links.canonical_youtube_url(VIDEO).startswith("https://www.youtube.com/watch?")


def test_slugify_falls_back_to_the_video_id():
    assert links.slugify("My Video: Part 2!") == "my-video-part-2"
    assert links.slugify("!!!", VIDEO) == "0a2bnryvco"


def test_unique_output_avoids_files_on_disk_and_queued_names(tmp_path):
    (tmp_path / "talk.md").write_text("x")
    taken = {tmp_path / "talk-2.md"}
    assert links.unique_output(tmp_path, "talk", taken) == tmp_path / "talk-3.md"


def test_collect_paths_keeps_dropped_files_and_filters_folders(tmp_path):
    odd = tmp_path / "notes.xyz"
    odd.write_text("x")
    folder = tmp_path / "docs"
    (folder / "deep").mkdir(parents=True)
    (folder / "a.pdf").write_text("x")
    (folder / "deep" / "b.DOCX").write_text("x")
    (folder / "skip.bin").write_text("x")
    found = links.collect_paths([str(odd), str(folder), str(tmp_path / "missing")])
    assert found == [odd, folder / "a.pdf", folder / "deep" / "b.DOCX"]
    assert all(isinstance(p, Path) for p in found)
