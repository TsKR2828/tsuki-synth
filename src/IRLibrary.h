#pragma once
#include <juce_audio_formats/juce_audio_formats.h>
#include <cstdint>
#include <vector>

// WF0908-P3 (F-03 IR_PRESET_RECALL, reports/decision_packets/
// F03_IR_PRESET_RECALL.zh-TW.md §7.1/§8 裁決記錄: 方案 B+ 受管理 IR 庫 +
// 工廠/使用者分流): a managed, content-addressed store for user-imported
// impulse responses, sibling to PresetManager's user-preset directory
// (src/PresetManager.h's getPresetDirectory() == %APPDATA%/TsukiSynth/
// Presets -- this lives at %APPDATA%/TsukiSynth/IR, i.e. "user preset 同層").
//
// Header-only, like PresetManager.h, so both GUI targets (TsukiSynth_VST3 /
// _Standalone, which link PluginProcessor.cpp) and the GUI-free HostProbe
// (tests/host_probe.cpp, which does NOT link PluginProcessor.cpp -- see that
// file's H7 header comment) can use it without a new CMakeLists.txt module
// link: SHA-256 (FIPS 180-4) is implemented locally below instead of pulling
// in the juce_cryptography module, which no target in this project currently
// links (card §5 GATE 4 restricts CMakeLists.txt changes to "add a new
// header, if needed" -- a self-contained hash keeps that need at zero).
namespace IRLibrary
{
    // Identity of one impulse response. kind=="user" is the only kind this
    // card implements (content-hash-addressed, see importFile()/resolve()
    // below); kind=="factory" + `id` is reserved per card §2.1 ("目前沒有
    // 工廈 IR ... 預留 IRRef.kind = user|factory") -- there is no factory IR
    // content yet (confirmed: no `data/` or BinaryData IR asset exists), so
    // no code path in this card ever constructs a factory IRRef.
    struct IRRef
    {
        juce::String kind = "user";   // "user" | "factory"
        juce::String sha256;          // full 64-hex-char content hash (kind=="user")
        juce::String originalName;    // filename at import time, for display
        juce::String id;              // factory catalogue id (kind=="factory", unused this card)

        bool isEmpty() const
        {
            return kind == "factory" ? id.isEmpty() : sha256.isEmpty();
        }
    };

    // ---- SHA-256 (FIPS 180-4), self-contained ----------------------------
    namespace detail
    {
        inline uint32_t rotr (uint32_t x, uint32_t n) { return (x >> n) | (x << (32 - n)); }

        inline juce::String sha256Hex (const void* data, size_t len)
        {
            static const uint32_t k[64] = {
                0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
                0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
                0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
                0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
                0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
                0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
                0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
                0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
            };
            uint32_t h[8] = { 0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                               0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19 };

            const auto* bytes = static_cast<const uint8_t*> (data);
            std::vector<uint8_t> msg (bytes, bytes + len);
            const uint64_t bitLen = (uint64_t) len * 8;
            msg.push_back (0x80);
            while (msg.size() % 64 != 56)
                msg.push_back (0);
            for (int i = 7; i >= 0; --i)
                msg.push_back ((uint8_t) (bitLen >> (i * 8)));

            for (size_t chunk = 0; chunk < msg.size(); chunk += 64)
            {
                uint32_t w[64];
                for (int i = 0; i < 16; ++i)
                    w[i] = (uint32_t (msg[chunk + (size_t) i * 4]) << 24)
                         | (uint32_t (msg[chunk + (size_t) i * 4 + 1]) << 16)
                         | (uint32_t (msg[chunk + (size_t) i * 4 + 2]) << 8)
                         |  uint32_t (msg[chunk + (size_t) i * 4 + 3]);
                for (int i = 16; i < 64; ++i)
                {
                    uint32_t s0 = rotr (w[i - 15], 7) ^ rotr (w[i - 15], 18) ^ (w[i - 15] >> 3);
                    uint32_t s1 = rotr (w[i - 2], 17) ^ rotr (w[i - 2], 19) ^ (w[i - 2] >> 10);
                    w[i] = w[i - 16] + s0 + w[i - 7] + s1;
                }
                uint32_t a = h[0], b = h[1], c = h[2], d = h[3];
                uint32_t e = h[4], f = h[5], g = h[6], hh = h[7];
                for (int i = 0; i < 64; ++i)
                {
                    uint32_t S1 = rotr (e, 6) ^ rotr (e, 11) ^ rotr (e, 25);
                    uint32_t ch = (e & f) ^ ((~e) & g);
                    uint32_t temp1 = hh + S1 + ch + k[i] + w[i];
                    uint32_t S0 = rotr (a, 2) ^ rotr (a, 13) ^ rotr (a, 22);
                    uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
                    uint32_t temp2 = S0 + maj;
                    hh = g; g = f; f = e; e = d + temp1;
                    d = c; c = b; b = a; a = temp1 + temp2;
                }
                h[0] += a; h[1] += b; h[2] += c; h[3] += d;
                h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
            }

            juce::String out;
            for (unsigned int hv : h)
                out += juce::String::toHexString ((juce::int64) hv).paddedLeft ('0', 8);
            return out.toLowerCase();
        }
    } // namespace detail

    /** Content hash of a file, or an empty string if it could not be read. */
    inline juce::String hashFile (const juce::File& file)
    {
        juce::MemoryBlock block;
        if (! file.loadFileAsData (block) || block.getSize() == 0)
            return {};
        return detail::sha256Hex (block.getData(), block.getSize());
    }

    /** <user preset 同層>/IR/ (卡 §2.1). Created on first access. */
    inline juce::File getDirectory()
    {
        auto dir = juce::File::getSpecialLocation (juce::File::userApplicationDataDirectory)
                       .getChildFile ("TsukiSynth")
                       .getChildFile ("IR");
        dir.createDirectory();
        return dir;
    }

    // 檔名 = <sha256 前 32 碼>.wav；旁邊 <同名>.json 記 metadata (卡 §2.1).
    inline juce::File fileForSha (const juce::String& sha256)
    {
        return getDirectory().getChildFile (sha256.substring (0, 32) + ".wav");
    }
    inline juce::File sidecarForSha (const juce::String& sha256)
    {
        return getDirectory().getChildFile (sha256.substring (0, 32) + ".json");
    }

    /** Resolve an IRRef to the library file that should hold it. Returns an
        invalid (non-existent) File() when the name-addressed file is not on
        disk -- the "找不到" case (card §2.3 row 3). This is a NAME lookup
        only; callers that need to know whether the resolved file's actual
        content still matches `ref.sha256` (the "指了別的檔" / corrupted-
        library case, §2.3 row 2) must re-hash it themselves via hashFile()
        -- see TsukiSynthProcessor::tryLoadIRRef(). */
    inline juce::File resolve (const IRRef& ref)
    {
        if (ref.kind != "user" || ref.sha256.isEmpty())
            return {};
        auto f = fileForSha (ref.sha256);
        return f.existsAsFile() ? f : juce::File();
    }

    /** Copy an external IR file into the managed library, deduplicated by
        content hash (re-importing identical bytes reuses the existing
        library entry -- "同檔改了名還是同一個 IR", decision packet §6.10.3).
        Returns an empty IRRef and fills `error` on failure. */
    inline IRRef importFile (const juce::File& source, juce::String& error)
    {
        if (! source.existsAsFile())
        {
            error = "File not found: " + source.getFullPathName();
            return {};
        }

        const auto sha = hashFile (source);
        if (sha.isEmpty())
        {
            error = "Failed to read/hash file: " + source.getFullPathName();
            return {};
        }

        auto dest = fileForSha (sha);
        if (! dest.existsAsFile())
        {
            if (! source.copyFileTo (dest))
            {
                error = "Failed to copy IR into library: " + dest.getFullPathName();
                return {};
            }
        }

        IRRef ref;
        ref.kind = "user";
        ref.sha256 = sha;
        ref.originalName = source.getFileName();

        // Sidecar metadata is informational (card §2.1); resolve()/mismatch
        // detection never read it back, so a write failure here does not
        // fail the import.
        juce::AudioFormatManager formats;
        formats.registerBasicFormats();
        std::unique_ptr<juce::AudioFormatReader> reader (formats.createReaderFor (dest));
        auto* meta = new juce::DynamicObject();
        meta->setProperty ("original_name", ref.originalName);
        meta->setProperty ("sha256", ref.sha256);
        meta->setProperty ("sample_rate", reader != nullptr ? reader->sampleRate : 0.0);
        meta->setProperty ("channels", reader != nullptr ? (int) reader->numChannels : 0);
        meta->setProperty ("imported_at", juce::Time::getCurrentTime().toISO8601 (true));
        sidecarForSha (sha).replaceWithText (juce::JSON::toString (juce::var (meta)));

        return ref;
    }

    /** All user IRs currently in the library, read from the .json sidecars. */
    inline juce::Array<IRRef> list()
    {
        juce::Array<IRRef> out;
        for (const auto& entry : juce::RangedDirectoryIterator (
                 getDirectory(), false, "*.json", juce::File::findFiles))
        {
            auto parsed = juce::JSON::parse (entry.getFile());
            if (! parsed.isObject())
                continue;
            IRRef ref;
            ref.kind = "user";
            ref.sha256 = parsed.getProperty ("sha256", juce::String()).toString();
            ref.originalName = parsed.getProperty ("original_name", juce::String()).toString();
            if (ref.sha256.isNotEmpty())
                out.add (ref);
        }
        return out;
    }
} // namespace IRLibrary
