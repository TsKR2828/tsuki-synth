#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "Presets.h"
#include <atomic>

class PresetManager : private juce::ValueTree::Listener
{
public:
    PresetManager (juce::AudioProcessorValueTreeState& vts)
        : apvts (vts), defaultState (vts.copyState())
    {
        reattachListener();
        scanUserPresets();
    }

    ~PresetManager() override
    {
        if (listenedState.isValid())
            listenedState.removeListener (this);
    }

    // ── Counts ──────────────────────────────────────────────────

    int getNumFactoryPresets() const
    {
        int c = 0;
        getFactoryPresetList (c);
        return c;
    }

    int getNumUserPresets() const
    {
        const juce::ScopedLock lock (presetLock);
        return userPresets.size();
    }
    int getNumPresets() const     { return getNumFactoryPresets() + getNumUserPresets(); }

    // ── Naming ──────────────────────────────────────────────────

    juce::String getPresetName (int index) const
    {
        int nFactory = getNumFactoryPresets();
        if (index >= 0 && index < nFactory)
        {
            int c = 0;
            auto* list = getFactoryPresetList (c);
            return list[index].name;
        }
        const juce::ScopedLock lock (presetLock);
        int ui = index - nFactory;
        if (ui >= 0 && ui < userPresets.size())
            return userPresets[ui].name;
        return {};
    }

    bool isFactory (int index) const { return index >= 0 && index < getNumFactoryPresets(); }

    // ── Load ────────────────────────────────────────────────────

    bool loadPreset (int index)
    {
        int nFactory = getNumFactoryPresets();
        bool loaded = false;

        if (index >= 0 && index < nFactory)
        {
            loaded = loadFactoryPreset (index);
        }
        else
        {
            int ui = index - nFactory;
            juce::ValueTree cachedState;
            {
                const juce::ScopedLock lock (presetLock);
                if (ui >= 0 && ui < userPresets.size())
                    cachedState = userPresets[ui].state.createCopy();
            }
            if (cachedState.isValid())
                loaded = loadUserState (cachedState);
        }

        if (! loaded)
            return false;

        currentIndex.store (index, std::memory_order_release);
        dirty.store (false, std::memory_order_release);
        return true;
    }

    // ── Init (reset all params to defaults) ─────────────────────

    void initPreset()
    {
        loading = true;
        apvts.replaceState (defaultState.createCopy());
        reattachListener();
        loading = false;
        currentIndex.store (-1, std::memory_order_release);
        dirty.store (false, std::memory_order_release);
    }

    /** Re-subscribe to the (potentially new) ValueTree after replaceState(). */
    void reattachListener()
    {
        if (listenedState.isValid())
            listenedState.removeListener (this);

        listenedState = apvts.state;
        if (listenedState.isValid())
            listenedState.addListener (this);
    }

    // ── Save user preset ────────────────────────────────────────

    bool userPresetExists (const juce::String& name) const
    {
        auto safeName = toSafeFilename (name);
        if (safeName.isEmpty()) return false;
        return getPresetDirectory().getChildFile (safeName + ".tsukipreset").existsAsFile();
    }

    bool saveUserPreset (const juce::String& name, bool allowOverwrite = false)
    {
        auto dir = getPresetDirectory();
        if (! dir.isDirectory())
            return false;

        auto safeName = toSafeFilename (name);
        if (safeName.isEmpty())
            return false;

        auto file = dir.getChildFile (safeName + ".tsukipreset");
        if (file.existsAsFile() && ! allowOverwrite)
            return false;

        auto state = apvts.copyState();
        auto stateXml = state.createXml();
        if (stateXml == nullptr)
            return false;

        juce::String presetId;
        if (file.existsAsFile())
            if (auto existing = juce::XmlDocument::parse (file))
                presetId = existing->getStringAttribute ("id");
        if (presetId.isEmpty())
            presetId = juce::Uuid().toString();

        juce::XmlElement root ("TsukiSynthPreset");
        root.setAttribute ("name", name);
        root.setAttribute ("id", presetId);
        root.setAttribute ("version", 2);
        root.addChildElement (stateXml.release());

        auto tempFile = file.getSiblingFile (file.getFileName() + ".tmp-"
                                              + juce::Uuid().toString());
        if (! root.writeTo (tempFile) || ! tempFile.replaceFileIn (file))
        {
            tempFile.deleteFile();
            return false;
        }

        scanUserPresets();

        int nFactory = getNumFactoryPresets();
        const juce::ScopedLock lock (presetLock);
        for (int i = 0; i < userPresets.size(); ++i)
        {
            if (userPresets[i].id == presetId)
            {
                currentIndex.store (nFactory + i, std::memory_order_release);
                break;
            }
        }
        dirty.store (false, std::memory_order_release);
        return true;
    }

    // ── Delete user preset ──────────────────────────────────────

    bool deleteUserPreset (int index)
    {
        int ui = index - getNumFactoryPresets();
        juce::File file;
        juce::String deletedId;
        juce::String activeId = getCurrentPresetId();
        {
            const juce::ScopedLock lock (presetLock);
            if (ui < 0 || ui >= userPresets.size())
                return false;
            file = userPresets[ui].file;
            deletedId = userPresets[ui].id;
        }

        if (! file.deleteFile())
            return false;
        scanUserPresets();

        if (activeId == deletedId)
        {
            // Do not claim that factory program 0 is loaded while retaining
            // the deleted preset's parameters.
            initPreset();
        }
        else if (activeId.isNotEmpty())
        {
            currentIndex.store (findPresetById (activeId), std::memory_order_release);
        }
        return true;
    }

    // ── State ───────────────────────────────────────────────────

    int  getCurrentIndex() const { return currentIndex.load (std::memory_order_acquire); }
    bool isDirty()         const { return dirty.load (std::memory_order_acquire); }
    void setDirty()              { dirty.store (true, std::memory_order_release); }
    void restoreDirty (bool value) { dirty.store (value, std::memory_order_release); }

    void setCurrentIndex (int i)
    {
        currentIndex.store (juce::jlimit (-1, getNumPresets() - 1, i),
                            std::memory_order_release);
        dirty.store (false, std::memory_order_release);
    }

    void restoreIndex (int i)
    {
        currentIndex.store (juce::jlimit (-1, getNumPresets() - 1, i),
                            std::memory_order_release);
    }

    juce::String getPresetId (int index) const
    {
        const int nFactory = getNumFactoryPresets();
        if (index >= 0 && index < nFactory)
        {
            int count = 0;
            auto* list = getFactoryPresetList (count);
            return "factory:" + juce::String (list[index].name);
        }

        const juce::ScopedLock lock (presetLock);
        const int ui = index - nFactory;
        return (ui >= 0 && ui < userPresets.size()) ? userPresets[ui].id
                                                    : juce::String();
    }

    juce::String getCurrentPresetId() const { return getPresetId (getCurrentIndex()); }

    int findPresetById (const juce::String& id) const
    {
        if (id.startsWith ("factory:"))
        {
            const auto wanted = id.fromFirstOccurrenceOf ("factory:", false, false);
            const int nFactory = getNumFactoryPresets();
            for (int i = 0; i < nFactory; ++i)
                if (getPresetName (i) == wanted)
                    return i;
            return -1;
        }

        const int nFactory = getNumFactoryPresets();
        const juce::ScopedLock lock (presetLock);
        for (int i = 0; i < userPresets.size(); ++i)
            if (userPresets[i].id == id)
                return nFactory + i;
        return -1;
    }

    // ── Scan disk ───────────────────────────────────────────────

    void scanUserPresets()
    {
        juce::Array<UserPreset> scanned;
        auto dir = getPresetDirectory();

        for (const auto& entry :
             juce::RangedDirectoryIterator (dir, false, "*.tsukipreset",
                                            juce::File::findFiles))
        {
            auto file = entry.getFile();
            auto xml  = juce::XmlDocument::parse (file);
            if (xml == nullptr)
                continue;

            juce::String name = xml->getStringAttribute ("name",
                                    file.getFileNameWithoutExtension());
            juce::String id = xml->getStringAttribute ("id");
            // Legacy v1 presets did not carry an ID.  A namespaced filename is
            // deterministic when the same preset file is copied to a machine.
            if (id.isEmpty())
                id = "legacy:" + file.getFileNameWithoutExtension();
            auto* paramsXml = xml->getChildByName (apvts.state.getType());
            if (paramsXml == nullptr)
                continue;
            auto state = juce::ValueTree::fromXml (*paramsXml);
            if (! state.isValid())
                continue;
            scanned.add ({ name, id, file, state });
        }

        struct NameCmp
        {
            int compareElements (const UserPreset& a, const UserPreset& b) const
            {
                return a.name.compareIgnoreCase (b.name);
            }
        };
        NameCmp cmp;
        scanned.sort (cmp);
        const juce::ScopedLock lock (presetLock);
        userPresets = std::move (scanned);
    }

private:
    struct UserPreset
    {
        juce::String name;
        juce::String id;
        juce::File   file;
        juce::ValueTree state;
    };

    juce::AudioProcessorValueTreeState& apvts;
    juce::ValueTree defaultState;
    juce::ValueTree listenedState;
    juce::Array<UserPreset> userPresets;
    mutable juce::CriticalSection presetLock;
    std::atomic<int> currentIndex { -1 };
    std::atomic<bool> dirty   { false };
    std::atomic<bool> loading { false };

    // ── ValueTree::Listener ─────────────────────────────────────

    void valueTreePropertyChanged (juce::ValueTree&, const juce::Identifier&) override
    {
        if (! loading)
            dirty = true;
    }

    void valueTreeChildAdded        (juce::ValueTree&, juce::ValueTree&)                  override {}
    void valueTreeChildRemoved      (juce::ValueTree&, juce::ValueTree&, int)             override {}
    void valueTreeChildOrderChanged  (juce::ValueTree&, int, int)                         override {}
    void valueTreeParentChanged      (juce::ValueTree&)                                   override {}

    // ── Factory preset loader ───────────────────────────────────

    bool loadFactoryPreset (int index)
    {
        int count = 0;
        auto* presets = getFactoryPresetList (count);
        if (index < 0 || index >= count)
            return false;

        loading = true;
        apvts.replaceState (defaultState.createCopy());
        reattachListener();

        const auto& preset = presets[index];
        for (int i = 0; i < preset.numParams; ++i)
        {
            const auto& entry = preset.params[i];
            if (auto* param = apvts.getParameter (entry.paramID))
            {
                float normalized = param->convertTo0to1 (entry.rawValue);
                param->setValueNotifyingHost (normalized);
            }
        }
        loading = false;
        return true;
    }

    // ── User preset file loader ─────────────────────────────────

    bool loadUserState (const juce::ValueTree& state)
    {
        if (! state.isValid() || state.getType() != apvts.state.getType())
            return false;

        loading = true;
        apvts.replaceState (state.createCopy());
        reattachListener();
        loading = false;
        return true;
    }

    // ── Helpers ─────────────────────────────────────────────────

    juce::File getPresetDirectory() const
    {
        auto dir = juce::File::getSpecialLocation (
                       juce::File::userApplicationDataDirectory)
                       .getChildFile ("TsukiSynth")
                       .getChildFile ("Presets");
        dir.createDirectory();
        return dir;
    }

    static juce::String toSafeFilename (const juce::String& name)
    {
        return name.removeCharacters ("/\\:*?\"<>|")
                   .trim()
                   .substring (0, 64);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PresetManager)
};
