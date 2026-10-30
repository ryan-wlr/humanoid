"""Convert one synchronized Isaac G1 raw episode into GR00T-LeRobot format.

Run this with the GR00T WSL environment after recording the raw JSON and MP4:
  python scripts/convert_g1_raw_demo_to_lerobot.py --raw <episode.json>
      --video <episode.mp4> --output <dataset-directory>
"""
import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

EXPECTED_JOINT_COUNT = 43
VIDEO_KEY = "observation.images.ego_view"


def _read_episode(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        episode = json.load(stream)
    if episode.get("recording_type") != "raw_simulated_demonstration":
        raise ValueError(f"{path} is not a raw simulated G1 demonstration.")
    if len(episode.get("joint_names", [])) != EXPECTED_JOINT_COUNT:
        raise ValueError("The episode must contain exactly 43 ordered G1 joints.")
    frames = episode.get("frames", [])
    if not frames:
        raise ValueError("The episode contains no frames.")
    for frame in frames:
        if len(frame["joint_position"]) != EXPECTED_JOINT_COUNT:
            raise ValueError("A state vector does not contain 43 values.")
        if len(frame["next_joint_position"]) != EXPECTED_JOINT_COUNT:
            raise ValueError("An action vector does not contain 43 values.")
    return episode


def _video_info(path: Path) -> tuple[int, float, int, int]:
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError(f"Could not open video: {path}")
        return (
            int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            float(capture.get(cv2.CAP_PROP_FPS)),
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    finally:
        capture.release()


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    episode = _read_episode(args.raw)
    if not args.video.is_file():
        raise FileNotFoundError(f"Video does not exist: {args.video}")
    video_frames, video_fps, width, height = _video_info(args.video)
    frames = episode["frames"]
    if video_frames != len(frames):
        raise ValueError(
            f"Video has {video_frames} frames but raw episode has {len(frames)} frames."
        )
    if not np.isclose(video_fps, episode["fps"], atol=0.01):
        raise ValueError(
            f"Video FPS {video_fps} does not match raw episode FPS {episode['fps']}."
        )

    output = args.output.resolve()
    data_dir = output / "data" / "chunk-000"
    video_dir = output / "videos" / "chunk-000" / VIDEO_KEY
    meta_dir = output / "meta"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")
    data_dir.mkdir(parents=True)
    video_dir.mkdir(parents=True)
    meta_dir.mkdir(parents=True)

    task = episode["task_description"]
    table = pa.table(
        {
            "observation.state": pa.array(
                [frame["joint_position"] for frame in frames],
                type=pa.list_(pa.float32(), EXPECTED_JOINT_COUNT),
            ),
            "action": pa.array(
                [frame["next_joint_position"] for frame in frames],
                type=pa.list_(pa.float32(), EXPECTED_JOINT_COUNT),
            ),
            "timestamp": pa.array([frame["timestamp"] for frame in frames], type=pa.float64()),
            "annotation.human.task_description": pa.array([0] * len(frames), type=pa.int64()),
            "task_index": pa.array([0] * len(frames), type=pa.int64()),
            "episode_index": pa.array([0] * len(frames), type=pa.int64()),
            "index": pa.array(range(len(frames)), type=pa.int64()),
            "next.reward": pa.array([0.0] * (len(frames) - 1) + [1.0], type=pa.float32()),
            "next.done": pa.array([False] * (len(frames) - 1) + [True], type=pa.bool_()),
        }
    )
    pq.write_table(table, data_dir / "episode_000000.parquet")
    shutil.copy2(args.video, video_dir / "episode_000000.mp4")

    modality = {
        "state": {
            "left_leg": {"start": 0, "end": 6},
            "right_leg": {"start": 6, "end": 12},
            "waist": {"start": 12, "end": 15},
            "left_arm": {"start": 15, "end": 22},
            "left_hand": {"start": 22, "end": 29},
            "right_arm": {"start": 29, "end": 36},
            "right_hand": {"start": 36, "end": 43},
        },
        "action": {
            "left_leg": {"start": 0, "end": 6},
            "right_leg": {"start": 6, "end": 12},
            "waist": {"start": 12, "end": 15},
            "left_arm": {"start": 15, "end": 22},
            "left_hand": {"start": 22, "end": 29},
            "right_arm": {"start": 29, "end": 36},
            "right_hand": {"start": 36, "end": 43},
        },
        "video": {"rs_view": {"original_key": VIDEO_KEY}},
        "annotation": {"human.task_description": {"original_key": "task_index"}},
    }
    info = {
        "codebase_version": "v2.0",
        "robot_type": "UnitreeG1",
        "total_episodes": 1,
        "total_frames": len(frames),
        "total_tasks": 1,
        "total_videos": 1,
        "total_chunks": 1,
        "chunks_size": 1000,
        "fps": episode["fps"],
        "splits": {"train": "0:1"},
        "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
        "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        "features": {
            VIDEO_KEY: {
                "dtype": "video",
                "shape": [height, width, 3],
                "names": ["height", "width", "channel"],
                "video_info": {
                    "video.fps": video_fps,
                    "video.codec": "mp4v",
                    "video.pix_fmt": "yuv420p",
                    "video.is_depth_map": False,
                    "has_audio": False,
                },
            },
            "observation.state": {
                "dtype": "float32",
                "shape": [EXPECTED_JOINT_COUNT],
                "names": episode["joint_names"],
            },
            "action": {
                "dtype": "float32",
                "shape": [EXPECTED_JOINT_COUNT],
                "names": episode["joint_names"],
            },
            "timestamp": {"dtype": "float64", "shape": [1]},
            "annotation.human.task_description": {"dtype": "int64", "shape": [1]},
            "task_index": {"dtype": "int64", "shape": [1]},
            "episode_index": {"dtype": "int64", "shape": [1]},
            "index": {"dtype": "int64", "shape": [1]},
            "next.reward": {"dtype": "float32", "shape": [1]},
            "next.done": {"dtype": "bool", "shape": [1]},
        },
    }
    (meta_dir / "info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    (meta_dir / "modality.json").write_text(json.dumps(modality, indent=2) + "\n", encoding="utf-8")
    _write_jsonl(meta_dir / "episodes.jsonl", [{"episode_index": 0, "tasks": [task], "length": len(frames)}])
    _write_jsonl(meta_dir / "tasks.jsonl", [{"task_index": 0, "task": task}])
    print(f"Created GR00T-LeRobot dataset: {output}")


if __name__ == "__main__":
    main()
