from faster_whisper import WhisperModel
from env_name import get_env_name
from typing import Union, Literal


def convert_to_subtitles_time_format(seconds: int, type: str) -> str:
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    if type == "vtt":
        str_time = "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)
    else:
        str_time = "%02d:%02d:%02d,%03d" % (hours, minutes, seconds, milliseconds)
    return str_time


def write_segments_to_vtt(segments, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for segment in segments:
            start_time = convert_to_subtitles_time_format(segment.start, "vtt")
            end_time = convert_to_subtitles_time_format(segment.end, "vtt")
            f.write("%s --> %s\n%s\n\n" % (start_time, end_time, segment.text))
            print("[%s --> %s] %s" % (start_time, end_time, segment.text))


def write_segments_to_srt(segments, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        segment_count = 1
        for segment in segments:
            start_time = convert_to_subtitles_time_format(segment.start, "srt")
            end_time = convert_to_subtitles_time_format(segment.end, "srt")
            text = segment.text

            f.write(f"{segment_count}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
            segment_count += 1
            print(f"[{start_time} --> {end_time}] {text}")


def transcribe(
    video_file_name: str,
    subtitles_format: Union[Literal["srt"], Literal["vtt"]],
    srt_file_name: str,
) -> None:

    # device="cpu"
    # compute_type="default"
    compute_type = "float16"
    device = "cuda"

    env_name = get_env_name()

    if env_name == "VSCode":
        device = "cpu"
        compute_type = "int8"

    assert subtitles_format in [
        "srt",
        "vvt",
    ], "subtitles_format יכול להיות רק 'srt' או 'vvt'"

    model_size = "large-v2"
    initial_prompt = "Hello, How is it going? Please, always use punctuation."
    model = WhisperModel(model_size, device, compute_type=compute_type)

    segments, info = model.transcribe(
        video_file_name,
        beam_size=5,
        language="he",
        initial_prompt=initial_prompt,
    )

    if subtitles_format == "srt":
        output_file = f"{srt_file_name}.srt"
        write_segments_to_srt(segments, output_file)
    else:
        output_file = f"{srt_file_name}.vtt"
        write_segments_to_vtt(segments, output_file)

    print("Transcription saved to", output_file)
