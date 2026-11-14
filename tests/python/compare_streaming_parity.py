"""Compare actual MATLAB and Python streamed fits, including a million rows."""

import argparse
import json
from pathlib import Path

import numpy as np

from pme_toolkit import backmap_streaming, fit_streaming, transform_streaming


def curve_rows(start, stop, rows, native):
    t = (np.arange(start, stop, dtype=float) + 0.5) / rows
    j = np.arange(1, 9, dtype=float)
    return (
        0.12 * np.sin(np.pi * t[:, None])
        + np.sin(np.pi * t[:, None] * j) @ ((0.04 / j ** 1.2)[:, None] * native)
        + 0.025 * np.sin(9 * np.pi * t[:, None]) * (native[0] * native[1])
    )


def compare(reference_path):
    fixture_path = Path(__file__).resolve().parents[1] / "data" / "snapshot_curve.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    references = json.loads(Path(reference_path).read_text(encoding="utf-8"))
    native = np.asarray(fixture["native"])
    query_native = np.asarray(fixture["query_native"])
    results = {}
    for label, rows in (("small", fixture["rows"]), ("large", fixture["large_rows"])):
        blocks = []
        requests = []

        def reader(start, stop):
            assert stop - start <= fixture["options"]["block_rows"]
            requests.append(stop - start)
            return curve_rows(start, stop, rows, native)

        def weights(start, stop):
            return np.full(stop - start, 1.0 / rows)

        def writer(start, stop, modes):
            blocks.append(modes.copy())

        model = fit_streaming(
            reader, (rows, native.shape[1]), weights, native, fixture["options"],
            ci=fixture["ci"], mode_writer=writer if label == "small" else None,
        )
        reference = references[label]
        assert model["nconf"] == int(reference["nconf"]) == fixture["selected_modes"]
        values = np.asarray(reference["eigenvalues"]).reshape(-1)
        np.testing.assert_allclose(model["eigenvalues"], values, rtol=1e-10, atol=1e-16)
        reference_vectors = np.asarray(reference["sample_vectors"])
        projector = model["sample_vectors"] @ model["sample_vectors"].T
        reference_projector = reference_vectors @ reference_vectors.T
        np.testing.assert_allclose(projector, reference_projector, atol=2e-11)
        reconstruction = backmap_streaming(model, model["coordinates"])
        np.testing.assert_allclose(reconstruction, reference["native_training"], rtol=1e-10, atol=2e-11)
        np.testing.assert_allclose(model["native_mean"].reshape(-1),
                                   np.asarray(reference["native_mean"]).reshape(-1), atol=2e-14)
        for key in ("total_variance", "achieved_ci", "eigenvalue_threshold"):
            np.testing.assert_allclose(model["info"][key], reference["info"][key],
                                       rtol=1e-10, atol=1e-16)
        assert model["info"]["numerical_rank"] == reference["info"]["numerical_rank"]
        results[label] = {
            "rows": rows,
            "samples": native.shape[1],
            "selected_modes": model["nconf"],
            "retained_variance": model["info"]["achieved_ci"],
            "maximum_eigenvalue_relative_error": float(np.max(np.abs(model["eigenvalues"] - values) / values)),
            "sample_projector_error": float(np.linalg.norm(projector - reference_projector)),
            "native_training_relative_error": float(
                np.linalg.norm(reconstruction - reference["native_training"]) / np.linalg.norm(reconstruction)
            ),
        }
        if label == "small":
            query_coordinates = transform_streaming(
                model, reader, lambda start, stop: curve_rows(start, stop, rows, query_native),
                query_native.shape[1], weights,
            )
            query_reconstruction = backmap_streaming(model, query_coordinates)
            np.testing.assert_allclose(query_reconstruction, reference["native_query"],
                                       rtol=1e-10, atol=2e-11)
            reconstructed_observations = np.vstack(blocks) @ model["coordinates"].T
            reference_observations = np.asarray(reference["observation_modes"]) @ np.asarray(reference["coordinates"]).T
            np.testing.assert_allclose(reconstructed_observations, reference_observations, atol=2e-12)
            results[label]["native_query_relative_error"] = float(
                np.linalg.norm(query_reconstruction - reference["native_query"]) / np.linalg.norm(query_reconstruction)
            )
        else:
            expected_blocks = (rows + fixture["options"]["block_rows"] - 1) // fixture["options"]["block_rows"]
            assert len(requests) == int(reference["reader_calls"]) == expected_blocks
            assert max(requests) == int(reference["max_block_rows"])
            assert not blocks
            results[label]["reader_calls"] = len(requests)
            results[label]["maximum_block_rows"] = max(requests)
        print(f"Streamed MATLAB/Python parity passed: Q={rows}, S={native.shape[1]}, N={model['nconf']}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = compare(args.reference)
    if args.output:
        args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
