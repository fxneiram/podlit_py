import os
import string

from fh.hfiles import FileManager


def test_sanitize_filename_strips_reserved_characters():
    manager = FileManager(temp_dir="unused", output_dir="unused")

    result = manager.sanitize_filename('Title: "A Story" <Part 1> / \\ | ? *')

    assert result == "Title_A_Story_Part_1_____"


def test_sanitize_filename_replaces_spaces_with_underscores():
    manager = FileManager(temp_dir="unused", output_dir="unused")

    assert manager.sanitize_filename("Hello World") == "Hello_World"


def test_sanitize_filename_can_produce_empty_string():
    """Edge case worth documenting, not fixing here: a title made entirely of reserved
    characters sanitizes to an empty string, so get_final_file_names would produce a bare
    ".wav"/".mp4" - a real but pre-existing limitation, out of scope for this test-coverage pass."""
    manager = FileManager(temp_dir="unused", output_dir="unused")

    assert manager.sanitize_filename("???") == ""


def test_get_final_file_names_builds_wav_and_mp4_paths(tmp_path):
    manager = FileManager(temp_dir=str(tmp_path / "tmp"), output_dir=str(tmp_path / "output"))

    audio_path, video_path = manager.get_final_file_names("My Book: Chapter 1")

    assert audio_path == str(tmp_path / "output" / "My_Book_Chapter_1.wav")
    assert video_path == str(tmp_path / "output" / "My_Book_Chapter_1.mp4")


def test_generate_random_path_has_expected_length_and_charset():
    manager = FileManager(temp_dir="unused", output_dir="unused")

    result = manager.generate_random_path(length=12)

    assert len(result) == 12
    assert all(char in string.ascii_letters + string.digits for char in result)


def test_generate_random_path_default_length_is_ten():
    manager = FileManager(temp_dir="unused", output_dir="unused")

    assert len(manager.generate_random_path()) == 10


def test_create_work_folders_creates_temp_and_output_dirs(tmp_path):
    temp_dir = tmp_path / "tmp"
    output_dir = tmp_path / "output"
    manager = FileManager(temp_dir=str(temp_dir), output_dir=str(output_dir))

    manager.create_work_folders()

    assert temp_dir.is_dir()
    assert output_dir.is_dir()


def test_create_work_folders_is_idempotent(tmp_path):
    temp_dir = tmp_path / "tmp"
    manager = FileManager(temp_dir=str(temp_dir), output_dir=str(tmp_path / "output"))

    manager.create_work_folders()
    manager.create_work_folders()  # should not raise

    assert temp_dir.is_dir()


def test_clean_temp_folders_removes_files_and_directory(tmp_path):
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    (temp_dir / "a.wav").write_bytes(b"")
    (temp_dir / "b.mp4").write_bytes(b"")
    manager = FileManager(temp_dir=str(temp_dir), output_dir=str(tmp_path / "output"))

    manager.clean_temp_folders()

    assert not temp_dir.exists()


def test_clean_temp_folders_on_empty_directory(tmp_path):
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    manager = FileManager(temp_dir=str(temp_dir), output_dir=str(tmp_path / "output"))

    manager.clean_temp_folders()

    assert not temp_dir.exists()


def test_default_dirs_come_from_config():
    from pkg import config as cfg

    manager = FileManager()

    assert manager.temp_dir == cfg.TEMP_DIR
    assert manager.output_dir == cfg.OUTPUT_DIR
    assert os.path.isabs(manager.temp_dir)
