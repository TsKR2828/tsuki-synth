"""Direct unit tests for the two WF0914-D14 streaming helpers in
tools/stem_verify.py (WF0925-P1, staged-review:D14-tests):

  * read_wav_header(path) -- returns (sample_rate, n_channels) from the
    'fmt ' chunk without reading the 'data' chunk. run() uses it to check a
    stem's sample rate / channel count against the reference mix.
  * StemArrayStream(entries) -- list-like, lazy view over stem WAV files that
    run() hands to compare_superposition() instead of a pre-built list.

Before this file they were only exercised indirectly by the end-to-end
stem_verify tests, which always read WAVs written by TsukiSynthCLI -- so the
RIFF edge cases below (a LIST chunk before 'fmt ', odd-sized chunks with
their pad byte, a WAVE_FORMAT_EXTENSIBLE fmt, fmt after data, an 18-byte
fmt) never reached them. Every WAV here is synthesized byte-by-byte in
Python (struct + numpy); no CLI is called. For every well-formed file the
header reader's (sr, ch) is compared with read_wav_float()'s, the reader the
superposition sum actually uses.

WF0925b-TF (decision packet O16): read_wav_float() now decodes
WAVE_FORMAT_EXTENSIBLE with a PCM / IEEE-float SubFormat GUID. The
test_extensible_* tests check that such a file gives exactly the samples of
the same payload under the plain tag, and that every other EXTENSIBLE shape
(other SubFormat, foreign GUID, short fmt, small cbSize, valid bits above
the container, 64-bit float) is still refused with ValueError.
"""

import importlib.util
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SPEC = importlib.util.spec_from_file_location(
    "stem_verify", ROOT / "tools" / "stem_verify.py")
sv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sv)

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE
# Microsoft's KSDATAFORMAT_SUBTYPE_* GUID tail, shared by PCM and IEEE float:
# {0000000X-0000-0010-8000-00AA00389B71}
_KSDATAFORMAT_TAIL = bytes([0x80, 0x00, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71])


# ---------------------------------------------------------------------------
# byte-level WAV builders
# ---------------------------------------------------------------------------

def _chunk(chunk_id, body, pad=True):
    """One RIFF chunk. The size field is len(body) (the pad byte is NOT
    counted, per RIFF); an odd-sized body is followed by one zero pad byte."""
    assert len(chunk_id) == 4
    out = chunk_id + struct.pack("<I", len(body)) + body
    if pad and len(body) % 2:
        out += b"\x00"
    return out


def _fmt_body(tag, n_channels, sample_rate, bits, extra=b""):
    block_align = n_channels * bits // 8
    return struct.pack("<HHIIHH", tag, n_channels, sample_rate,
                       sample_rate * block_align, block_align, bits) + extra


def _extensible_extra(bits, channel_mask, sub_format_tag):
    """cbSize=22 + wValidBitsPerSample + dwChannelMask + SubFormat GUID,
    i.e. the 24 bytes that make a 40-byte WAVE_FORMAT_EXTENSIBLE fmt."""
    guid = struct.pack("<IHH", sub_format_tag, 0x0000, 0x0010) + _KSDATAFORMAT_TAIL
    return struct.pack("<HHI", 22, bits, channel_mask) + guid


def _riff(chunks):
    body = b"WAVE" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def _pcm16(arr):
    return np.round(np.asarray(arr) * 32767.0).astype("<i2").tobytes()


def _float32(arr):
    return np.asarray(arr, dtype="<f4").tobytes()


def _stereo_ramp(n, scale=0.5):
    left = np.linspace(-scale, scale, n)
    right = -left
    return np.stack([left, right], axis=1)


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _assert_header_matches_float(path, expected_sr, expected_ch):
    sr_h, ch_h = sv.read_wav_header(path)
    sr_f, ch_f, arr = sv.read_wav_float(path)
    assert (sr_h, ch_h) == (expected_sr, expected_ch)
    assert (sr_h, ch_h) == (sr_f, ch_f), (
        "read_wav_header says (%d, %d) but read_wav_float says (%d, %d)"
        % (sr_h, ch_h, sr_f, ch_f))
    assert arr.shape[1] == expected_ch
    return arr


# ---------------------------------------------------------------------------
# read_wav_header: well-formed edge cases, cross-checked with read_wav_float
# ---------------------------------------------------------------------------

def test_header_plain_pcm16_matches_float(tmp_path):
    frames = _stereo_ramp(64)
    data = _riff([_chunk(b"fmt ", _fmt_body(WAVE_FORMAT_PCM, 2, 44100, 16)),
                  _chunk(b"data", _pcm16(frames))])
    path = _write(tmp_path, "plain.wav", data)
    arr = _assert_header_matches_float(path, 44100, 2)
    np.testing.assert_array_equal(
        arr, np.frombuffer(_pcm16(frames), dtype="<i2").reshape(-1, 2) / 32768.0)


def test_header_skips_list_chunk_before_fmt(tmp_path):
    # A LIST/INFO chunk ahead of 'fmt ' (what many editors write) must be
    # skipped by size, not mistaken for the format chunk.
    info = _chunk(b"INAM", b"stem title\x00")  # 11-byte body -> padded
    list_body = b"INFO" + info
    frames = _stereo_ramp(32)
    data = _riff([_chunk(b"LIST", list_body),
                  _chunk(b"fmt ", _fmt_body(WAVE_FORMAT_IEEE_FLOAT, 2, 48000, 32)),
                  _chunk(b"data", _float32(frames))])
    path = _write(tmp_path, "list_first.wav", data)
    arr = _assert_header_matches_float(path, 48000, 2)
    np.testing.assert_array_equal(arr, frames.astype(np.float32).astype(np.float64))


@pytest.mark.parametrize("odd_size", [1, 5, 7])
def test_header_odd_sized_chunk_pad_byte(tmp_path, odd_size):
    # Odd-sized chunks are followed by a pad byte that is NOT in the size
    # field. One sits before 'fmt ' (read_wav_header's walk) and one between
    # 'fmt ' and 'data' (read_wav_float's walk).
    frames = _stereo_ramp(16)
    junk = _chunk(b"junk", bytes(range(odd_size)))
    note = _chunk(b"note", b"x" * odd_size)
    # make sure the fixture really has the property under test
    assert len(junk) == 8 + odd_size + 1
    assert struct.unpack("<I", junk[4:8])[0] == odd_size
    data = _riff([junk,
                  _chunk(b"fmt ", _fmt_body(WAVE_FORMAT_PCM, 1, 22050, 16)),
                  note,
                  _chunk(b"data", _pcm16(frames[:, 0]))])
    path = _write(tmp_path, "odd_%d.wav" % odd_size, data)
    arr = _assert_header_matches_float(path, 22050, 1)
    np.testing.assert_array_equal(
        arr[:, 0], np.frombuffer(_pcm16(frames[:, 0]), dtype="<i2") / 32768.0)


def test_header_fmt_with_cbsize_18_bytes(tmp_path):
    # PCM fmt carrying a cbSize field (18-byte body). Both readers must use
    # the chunk's own size to step over it rather than assuming 16.
    frames = _stereo_ramp(20)
    fmt = _fmt_body(WAVE_FORMAT_PCM, 2, 32000, 16, extra=struct.pack("<H", 0))
    assert len(fmt) == 18
    data = _riff([_chunk(b"fmt ", fmt), _chunk(b"data", _pcm16(frames))])
    path = _write(tmp_path, "fmt18.wav", data)
    _assert_header_matches_float(path, 32000, 2)


def test_header_fmt_after_data(tmp_path):
    # Out-of-order but parseable: read_wav_header must seek past 'data'
    # (without loading it) to reach 'fmt '; read_wav_float accepts either
    # order too, so both must agree.
    frames = _stereo_ramp(40)
    data = _riff([_chunk(b"data", _pcm16(frames)),
                  _chunk(b"fmt ", _fmt_body(WAVE_FORMAT_PCM, 2, 96000, 16))])
    path = _write(tmp_path, "fmt_after_data.wav", data)
    _assert_header_matches_float(path, 96000, 2)


def test_header_extensible_fmt(tmp_path):
    # WAVE_FORMAT_EXTENSIBLE (0xFFFE, 40-byte fmt). read_wav_header only
    # needs the first 16 bytes, so it reports sr/ch correctly.
    # WF0925b-TF (decision packet O16): read_wav_float now DECODES tag 0xFFFE
    # with a PCM / IEEE-float SubFormat GUID (it used to refuse it with
    # "unsupported wav format"); the same file must give exactly the samples
    # of the plain-tag file. Unsupported SubFormats still refuse loudly --
    # see the test_extensible_* tests below.
    frames = _stereo_ramp(24)
    extra = _extensible_extra(bits=16, channel_mask=0x3,
                              sub_format_tag=WAVE_FORMAT_PCM)
    fmt = _fmt_body(WAVE_FORMAT_EXTENSIBLE, 2, 48000, 16, extra=extra)
    assert len(fmt) == 40
    data = _riff([_chunk(b"LIST", b"INFO"),
                  _chunk(b"fmt ", fmt),
                  _chunk(b"data", _pcm16(frames))])
    path = _write(tmp_path, "extensible.wav", data)

    assert sv.read_wav_header(path) == (48000, 2)
    arr = _assert_header_matches_float(path, 48000, 2)
    np.testing.assert_array_equal(
        arr, np.frombuffer(_pcm16(frames), dtype="<i2").reshape(-1, 2) / 32768.0)


# ---------------------------------------------------------------------------
# read_wav_float: WAVE_FORMAT_EXTENSIBLE decoding (WF0925b-TF, O16)
# ---------------------------------------------------------------------------

def _pcm24(arr):
    v = np.round(np.asarray(arr).reshape(-1) * 8388607.0).astype(np.int64)
    v = np.where(v < 0, v + (1 << 24), v).astype(np.uint32)
    b = np.stack([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF], axis=1)
    return b.astype(np.uint8).tobytes()


def _pcm32_left_justified_24(arr):
    # 24 valid bits in a 32-bit container: the sample sits in the top 24
    # bits and the low 8 bits are zero (WAVEFORMATEXTENSIBLE convention).
    v = np.round(np.asarray(arr).reshape(-1) * 8388607.0).astype(np.int64) << 8
    return v.astype("<i4").tobytes()


def _extensible_and_plain(tmp_path, name, plain_tag, bits, valid_bits, payload,
                          n_channels=2, sample_rate=48000, channel_mask=0x3):
    """The same payload written twice: once with the plain tag, once as
    WAVE_FORMAT_EXTENSIBLE with the matching SubFormat GUID."""
    plain = _riff([_chunk(b"fmt ", _fmt_body(plain_tag, n_channels, sample_rate, bits)),
                   _chunk(b"data", payload)])
    extra = _extensible_extra(bits=valid_bits, channel_mask=channel_mask,
                              sub_format_tag=plain_tag)
    ext = _riff([_chunk(b"fmt ", _fmt_body(WAVE_FORMAT_EXTENSIBLE, n_channels,
                                           sample_rate, bits, extra=extra)),
                 _chunk(b"data", payload)])
    return (_write(tmp_path, name + "_plain.wav", plain),
            _write(tmp_path, name + "_ext.wav", ext))


@pytest.mark.parametrize("case", ["pcm16", "pcm24", "pcm32", "pcm32_valid24", "float32"])
def test_extensible_decodes_identically_to_plain_tag(tmp_path, case):
    frames = _stereo_ramp(48, scale=0.9)
    if case == "pcm16":
        args = (WAVE_FORMAT_PCM, 16, 16, _pcm16(frames))
    elif case == "pcm24":
        args = (WAVE_FORMAT_PCM, 24, 24, _pcm24(frames))
    elif case == "pcm32":
        payload = np.round(frames.reshape(-1) * 2147483647.0).astype("<i4").tobytes()
        args = (WAVE_FORMAT_PCM, 32, 32, payload)
    elif case == "pcm32_valid24":
        args = (WAVE_FORMAT_PCM, 32, 24, _pcm32_left_justified_24(frames))
    else:
        args = (WAVE_FORMAT_IEEE_FLOAT, 32, 32, _float32(frames))
    tag, bits, valid_bits, payload = args
    plain_path, ext_path = _extensible_and_plain(tmp_path, case, tag, bits,
                                                 valid_bits, payload)
    sr_p, ch_p, arr_p = sv.read_wav_float(plain_path)
    sr_e, ch_e, arr_e = sv.read_wav_float(ext_path)
    assert (sr_e, ch_e) == (sr_p, ch_p) == (48000, 2)
    assert arr_e.shape == arr_p.shape == (48, 2)
    np.testing.assert_array_equal(arr_e, arr_p)
    # and the numbers are the intended ones, not merely equal to each other
    np.testing.assert_allclose(arr_e, frames, atol=1e-4)


def test_extensible_float_guid_is_not_decoded_as_pcm(tmp_path):
    # Mutation guard: a reader that ignored the SubFormat GUID and fell back
    # to "32-bit = PCM int" would return garbage for float data. The float
    # GUID must yield the float samples themselves.
    frames = _stereo_ramp(16, scale=0.25)
    _plain, ext_path = _extensible_and_plain(tmp_path, "floatguid",
                                             WAVE_FORMAT_IEEE_FLOAT, 32, 32,
                                             _float32(frames))
    _sr, _ch, arr = sv.read_wav_float(ext_path)
    np.testing.assert_array_equal(arr, frames.astype(np.float32).astype(np.float64))
    as_int = np.frombuffer(_float32(frames), dtype="<i4").reshape(-1, 2) / 2147483648.0
    assert not np.array_equal(arr, as_int)


def _extensible_file(tmp_path, name, fmt_extra, bits=16, payload=None):
    fmt = _fmt_body(WAVE_FORMAT_EXTENSIBLE, 2, 48000, bits, extra=fmt_extra)
    payload = payload if payload is not None else _pcm16(_stereo_ramp(8))
    return _write(tmp_path, name, _riff([_chunk(b"fmt ", fmt), _chunk(b"data", payload)]))


def test_extensible_unsupported_subformat_tag_is_refused(tmp_path):
    # KSDATAFORMAT GUID shape but sub-tag 6 (A-law): not decoded, refused.
    path = _extensible_file(tmp_path, "alaw.wav",
                            _extensible_extra(bits=16, channel_mask=0x3, sub_format_tag=0x0006))
    with pytest.raises(ValueError, match="unsupported WAVE_FORMAT_EXTENSIBLE SubFormat"):
        sv.read_wav_float(path)


def test_extensible_foreign_guid_is_refused(tmp_path):
    # First field says PCM, but the rest of the GUID is not the
    # KSDATAFORMAT tail -- a vendor-specific format. Must be refused, not
    # decoded as PCM because the first 4 bytes happen to read 1.
    guid = struct.pack("<IHH", WAVE_FORMAT_PCM, 0x1234, 0x5678) + bytes(range(8))
    extra = struct.pack("<HHI", 22, 16, 0x3) + guid
    path = _extensible_file(tmp_path, "vendor.wav", extra)
    with pytest.raises(ValueError, match="unsupported WAVE_FORMAT_EXTENSIBLE SubFormat"):
        sv.read_wav_float(path)


def test_extensible_short_fmt_is_refused(tmp_path):
    # tag 0xFFFE but only an 18-byte fmt (cbSize=0): the extension the tag
    # promises is missing.
    path = _extensible_file(tmp_path, "short_ext.wav", struct.pack("<H", 0))
    with pytest.raises(ValueError, match="needs 40"):
        sv.read_wav_float(path)


def test_extensible_small_cbsize_is_refused(tmp_path):
    extra = bytearray(_extensible_extra(bits=16, channel_mask=0x3,
                                        sub_format_tag=WAVE_FORMAT_PCM))
    extra[0:2] = struct.pack("<H", 10)  # cbSize says 10, needs 22
    path = _extensible_file(tmp_path, "cbsize10.wav", bytes(extra))
    with pytest.raises(ValueError, match="cbSize=10"):
        sv.read_wav_float(path)


def test_extensible_valid_bits_above_container_is_refused(tmp_path):
    path = _extensible_file(tmp_path, "valid20.wav",
                            _extensible_extra(bits=20, channel_mask=0x3,
                                              sub_format_tag=WAVE_FORMAT_PCM))
    with pytest.raises(ValueError, match="wValidBitsPerSample=20"):
        sv.read_wav_float(path)


def test_extensible_float64_still_unsupported(tmp_path):
    # A valid IEEE-float GUID but a 64-bit container: the plain tag-3 64-bit
    # case is not decoded either, so this must refuse with the same message
    # family, naming the EXTENSIBLE origin.
    payload = np.asarray(_stereo_ramp(8), dtype="<f8").tobytes()
    path = _extensible_file(tmp_path, "f64.wav",
                            _extensible_extra(bits=64, channel_mask=0x3,
                                              sub_format_tag=WAVE_FORMAT_IEEE_FLOAT),
                            bits=64, payload=payload)
    with pytest.raises(ValueError,
                       match=r"unsupported wav format \(tag=3 bits=64, from WAVE_FORMAT_EXTENSIBLE"):
        sv.read_wav_float(path)


def test_header_does_not_need_data_bytes(tmp_path):
    # 'data' declares far more bytes than the file holds. The header reader
    # answers from 'fmt ' alone and returns before touching 'data'.
    data = _riff([_chunk(b"fmt ", _fmt_body(WAVE_FORMAT_PCM, 2, 44100, 16))])
    data += b"data" + struct.pack("<I", 1_000_000_000) + b"\x00" * 8
    path = _write(tmp_path, "truncated_data.wav", data)
    assert sv.read_wav_header(path) == (44100, 2)


# ---------------------------------------------------------------------------
# read_wav_header: malformed input is refused, not guessed
# ---------------------------------------------------------------------------

def test_header_rejects_non_riff(tmp_path):
    path = _write(tmp_path, "not_riff.wav", b"RIFX" + b"\x00" * 40)
    with pytest.raises(ValueError, match="not a RIFF/WAVE"):
        sv.read_wav_header(path)


def test_header_rejects_missing_fmt(tmp_path):
    data = _riff([_chunk(b"data", _pcm16(_stereo_ramp(8)))])
    path = _write(tmp_path, "no_fmt.wav", data)
    with pytest.raises(ValueError, match="no fmt chunk"):
        sv.read_wav_header(path)
    with pytest.raises(ValueError, match="no fmt chunk"):
        sv.read_wav_float(path)


def test_header_rejects_truncated_fmt(tmp_path):
    data = _riff([]) + b"fmt " + struct.pack("<I", 16) + b"\x01\x00\x02\x00"
    path = _write(tmp_path, "short_fmt.wav", data)
    with pytest.raises(ValueError, match="truncated fmt"):
        sv.read_wav_header(path)


# ---------------------------------------------------------------------------
# StemArrayStream: len / iteration semantics
# ---------------------------------------------------------------------------

def _stem_files(tmp_path, n_samples_list, sr=48000):
    """Float32 stereo stems with distinct content and lengths; returns
    (entries, arrays) where arrays[i] is exactly what read_wav_float gives
    back for entries[i]'s file."""
    entries, arrays = [], []
    for i, n in enumerate(n_samples_list):
        frames = _stereo_ramp(n, scale=0.1 * (i + 1)).astype(np.float32)
        data = _riff([_chunk(b"fmt ", _fmt_body(WAVE_FORMAT_IEEE_FLOAT, 2, sr, 32)),
                      _chunk(b"data", _float32(frames))])
        path = _write(tmp_path, "stem_%02d.wav" % i, data)
        # orig_idx deliberately not 0..n-1, to show order follows `entries`
        entries.append((10 * i + 3, path))
        arrays.append(frames.astype(np.float64))
    return entries, arrays


def test_stream_len_and_order(tmp_path):
    entries, arrays = _stem_files(tmp_path, [50, 30, 70])
    stream = sv.StemArrayStream(entries)
    assert len(stream) == 3
    got = list(stream)
    assert len(got) == 3
    for g, want, (_idx, path) in zip(got, arrays, entries):
        np.testing.assert_array_equal(g, want)
        np.testing.assert_array_equal(g, sv.read_wav_float(path)[2])

    reversed_stream = sv.StemArrayStream(list(reversed(entries)))
    for g, want in zip(reversed_stream, reversed(arrays)):
        np.testing.assert_array_equal(g, want)


def test_stream_reads_lazily_one_file_at_a_time(tmp_path, monkeypatch):
    entries, _arrays = _stem_files(tmp_path, [10, 20, 30])
    real_read = sv.read_wav_float
    calls = []

    def counting_read(path):
        calls.append(Path(path).name)
        return real_read(path)

    monkeypatch.setattr(sv, "read_wav_float", counting_read)
    stream = sv.StemArrayStream(entries)
    assert calls == []            # construction reads nothing
    assert len(stream) == 3
    assert calls == []            # len() reads nothing

    it = iter(stream)
    assert calls == []            # creating the iterator reads nothing
    first = next(it)
    assert calls == ["stem_00.wav"]
    assert first.shape == (10, 2)
    second = next(it)
    assert calls == ["stem_00.wav", "stem_01.wav"]
    assert second.shape == (20, 2)
    third = next(it)
    assert calls == ["stem_00.wav", "stem_01.wav", "stem_02.wav"]
    assert third.shape == (30, 2)
    with pytest.raises(StopIteration):
        next(it)
    assert len(calls) == 3


def test_stream_is_reiterable(tmp_path):
    # A plain list can be iterated more than once; so can the stream (each
    # iter() starts a fresh pass over the files).
    entries, arrays = _stem_files(tmp_path, [12, 8])
    stream = sv.StemArrayStream(entries)
    first_pass = list(stream)
    second_pass = list(stream)
    assert len(first_pass) == len(second_pass) == len(stream) == 2
    for a, b, want in zip(first_pass, second_pass, arrays):
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(a, want)


def test_stream_empty(tmp_path):
    stream = sv.StemArrayStream([])
    assert len(stream) == 0
    assert list(stream) == []


def test_compare_superposition_same_result_for_stream_and_list(tmp_path):
    # compare_superposition() only uses len() and iteration on its stem
    # argument; feeding it the stream must give the identical result dict
    # to feeding it the materialized list, including n_stems_summed.
    entries, arrays = _stem_files(tmp_path, [40, 64, 25])
    n = max(a.shape[0] for a in arrays)
    reference = np.zeros((n, 2), dtype=np.float64)
    for a in arrays:
        reference[: a.shape[0]] += a
    reference[5, 0] += 1e-3  # make it non-exact so the residual fields are filled

    from_list = sv.compare_superposition(reference, list(arrays), 48000)
    from_stream = sv.compare_superposition(
        reference, sv.StemArrayStream(entries), 48000)
    assert from_stream == from_list
    assert from_stream["n_stems_summed"] == 3
    assert from_stream["bit_exact"] is False
    assert from_stream["first_diff_sample_index"] == 5
